# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Helper functions for managing parameters. """

from jsonschema import validate, ValidationError
from six import iteritems

from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.sql import or_

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import (PersonalityStage, PersonalityParameter, Host,
                                FeatureLink, HostFeature, HardwareFeature,
                                HardwareEntity, Interface)
from aquilon.aqdb.model.hostlifecycle import Ready, Almostready
from aquilon.worker.formats.parameter_definition import ParamDefinitionFormatter
from aquilon.worker.templates import Plenary, PlenaryHost, PlenaryPersonality


def set_parameter(session, parameter, db_paramdef, path, value, update=False):
    """
        Handles add parameter as well as update parameter. Parmeters for features
        will be stored as part of personality as features/<feature_name>/<path>
    """
    retval = db_paramdef.parse_value(path, value)
    if db_paramdef.activation == 'rebuild':
        validate_rebuild_required(session, path, parameter.personality_stage)

    parameter.set_path(path, retval, update)

    if db_paramdef.schema:
        new_value = parameter.get_path(db_paramdef.path)
        try:
            validate(new_value, db_paramdef.schema)
        except ValidationError as err:
            raise ArgumentError(err)


def del_all_feature_parameter(session, dblink):
    dbstage = dblink.personality_stage
    defholder = dblink.feature.param_def_holder

    if not dbstage or not defholder:
        return

    try:
        parameter = dbstage.parameters[defholder]
    except KeyError:
        return

    for link in dbstage.features:
        # If the feature is still bound, then leave the parameters alone
        if link.feature == dblink.feature and link != dblink:
            break
    else:
        for paramdef in defholder.param_definitions:
            if paramdef.activation != 'rebuild':
                continue

            value = parameter.get_path(paramdef.path, compel=False)
            if value is not None:
                validate_rebuild_required(session, paramdef.path, dbstage)

        del dbstage.parameters[defholder]


def validate_rebuild_required(session, path, dbstage):
    """ check if this parameter requires hosts to be in non-ready state
    """
    dbready = Ready.get_instance(session)
    dbalmostready = Almostready.get_instance(session)

    q = session.query(Host.hardware_entity_id)
    q = q.filter(or_(Host.status == dbready, Host.status == dbalmostready))
    q = q.filter_by(personality_stage=dbstage)
    if q.count():
        raise ArgumentError("Modifying parameter %s value needs a host rebuild. "
                            "There are hosts associated to the personality in non-ready state. "
                            "Please set these host to status of rebuild to continue. "
                            "Run 'aq search host --personality %s --buildstatus ready' "
                            "and 'aq search host --personality %s --buildstatus almostready' to "
                            "get the list of the affected hosts." %
                            (path, dbstage, dbstage))


def lookup_paramdef(holder_object, path, strict=True):
    """
    Return the definition belonging the given parameter path.

    If the strict parameter is false, then the path may point inside a
    JSON-typed definition.
    """

    if hasattr(holder_object, 'param_def_holder'):
        # Feature
        param_def_holder = holder_object.param_def_holder
        if not param_def_holder:
            raise NotFoundException("No parameter definitions found for {0:l}."
                                    .format(holder_object))
        rel_path = path
    else:
        # Archetype - the path in the parameter definition contains the name of
        # the template, but the relative path we want to return should not
        if "/" in path:
            template, rel_path = path.split("/", 1)
        else:
            template, rel_path = path, ""

        try:
            param_def_holder = holder_object.param_def_holders[template]
        except KeyError:
            raise ArgumentError("Unknown parameter template %s." % template)

    for db_paramdef in param_def_holder.param_definitions:
        if rel_path == db_paramdef.path:
            return db_paramdef, rel_path

        # Allow "indexing into" JSON parameters, but only if the path is not
        # strictly for the definition
        if strict or db_paramdef.value_type != "json":
            continue

        if db_paramdef.path == "" or rel_path.startswith(db_paramdef.path + "/"):
            return db_paramdef, rel_path

    raise NotFoundException("Path {0!s} does not match any parameter "
                            "definitions of {1:l}."
                            .format(path, holder_object))


def validate_required_parameter(param_def_holder, parameter):
    errors = []
    formatter = ParamDefinitionFormatter()
    for param_def in param_def_holder.param_definitions:
        # ignore not required fields or fields
        # which have defaults specified
        if (not param_def.required) or param_def.default is not None:
            continue

        if parameter:
            value = parameter.get_path(param_def.path, compel=False)
        else:
            value = None

        if value is None:
            errors.append(formatter.format_raw(param_def))

    return errors


def search_path_in_personas(session, db_paramdef, path=None):
    q = session.query(PersonalityParameter)
    q = q.filter_by(param_def_holder=db_paramdef.holder)
    q = q.options(joinedload('personality_stage'),
                  joinedload('personality_stage.personality'))

    params = {}

    if not path:
        path = db_paramdef.path

    for parameter in q:
        try:
            value = parameter.get_path(path)
            if value is not None:
                params[parameter] = value
        except NotFoundException:
            pass
    return params


def validate_personality_config(dbstage):
    """
        Validates all the parameters on personality to validate
        if all required parameters have been set. All feature
        parameters are also validated.
    """
    dbarchetype = dbstage.personality.archetype
    error = []

    # Validate archetype-wide parameters
    for param_def_holder in dbarchetype.param_def_holders.values():
        parameter = dbstage.parameters.get(param_def_holder, None)
        error += validate_required_parameter(param_def_holder, parameter)

    # Validate feature parameters
    for dbfeature in dbstage.param_features:
        param_def_holder = dbfeature.param_def_holder
        parameter = dbstage.parameters.get(param_def_holder, None)
        tmp_error = validate_required_parameter(param_def_holder, parameter)
        if tmp_error:
            error.append("Feature Binding: %s" % dbfeature)
            error += tmp_error

    return error


def add_arch_paramdef_plenaries(session, param_def_holder, plenaries):
    q = session.query(PersonalityParameter)
    q = q.filter_by(param_def_holder=param_def_holder)
    q = q.options(joinedload('personality_stage'),
                  joinedload('personality_stage.personality'))
    plenaries.extend(Plenary.get_plenary(dbparam) for dbparam in q)


def add_feature_paramdef_plenaries(session, dbfeature, plenaries):
    if isinstance(dbfeature, HostFeature):
        q = session.query(PersonalityStage)

        q = q.join(PersonalityStage.features)
        q = q.filter_by(feature=dbfeature)
        q = q.options(PlenaryPersonality.query_options())
        plenaries.extend(map(Plenary.get_plenary, q))
    else:
        q = session.query(Host)
        q = q.join(PersonalityStage, FeatureLink)
        q = q.filter_by(feature=dbfeature)
        q = q.reset_joinpoint()

        q = q.join(HardwareEntity)
        if isinstance(dbfeature, HardwareFeature):
            q = q.filter(FeatureLink.model_id == HardwareEntity.model_id)
        else:
            q = q.join(Interface)
            q = q.filter(or_(FeatureLink.interface_name == Interface.name,
                             FeatureLink.model_id == Interface.model_id))

        q = q.options(contains_eager('hardware_entity'),
                      contains_eager('personality_stage'))
        q = q.options(PlenaryHost.query_options())

        plenaries.extend(map(Plenary.get_plenary, q))


def update_paramdef_schema(session, db_paramdef, schema):
    if db_paramdef.value_type != "json":
        raise ArgumentError("Only JSON parameters may have a schema.")
    db_paramdef.schema = schema

    # Ensure that existing values do not conflict with the new schema
    params = search_path_in_personas(session, db_paramdef)
    for param, value in iteritems(params):
        try:
            validate(value, schema)
        except ValidationError as err:
            raise ArgumentError("Existing value for {0:l} conflicts with the "
                                "new schema: {1!s}"
                                .format(param.holder_object, err))
