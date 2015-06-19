# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

import re

from sqlalchemy.orm import contains_eager, subqueryload
from sqlalchemy.sql import or_

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.utils import (force_json_dict, force_int, force_float,
                           force_boolean)
from aquilon.aqdb.model import (Personality, PersonalityStage, Parameter,
                                Feature, FeatureLink, Host, Model,
                                ParamDefinition, ArchetypeParamDef,
                                PersonalityParameter)
from aquilon.aqdb.model.hostlifecycle import Ready, Almostready
from aquilon.worker.formats.parameter_definition import ParamDefinitionFormatter


def get_feature_link(session, feature, model, interface_name, dbstage):
    feature_type = 'host'
    if interface_name:
        feature_type = 'interface'
    if model:
        dbmodel = Model.get_unique(session, name=model,
                                   compel=True)
        if dbmodel.model_type.isNic():
            feature_type = 'interface'
        else:
            if interface_name:
                raise ArgumentError("{0} is not a network interface model."
                                    .format(dbmodel))
            feature_type = 'hardware'
    else:
        dbmodel = None

    dbfeature = Feature.get_unique(session, name=feature,
                                   feature_type=feature_type, compel=True)
    dblink = FeatureLink.get_unique(session, feature=dbfeature,
                                    interface_name=interface_name,
                                    model=dbmodel,
                                    personality_stage=dbstage, compel=True)
    return dblink


def set_parameter(session, param_holder, dblink, path, value, compel=False,
                  preclude=False):
    """
        Handles add parameter as well as update parameter. Parmeters for features
        will be stored as part of personality as features/<feature_name>/<path>
    """
    parameter = param_holder.parameter

    retval = validate_parameter(session, path, value, param_holder, dblink)

    if dblink:
        path = Parameter.feature_path(dblink, path)
    parameter.set_path(path, retval, compel, preclude)


def del_parameter(session, path, param_holder, dblink):
    parameter = param_holder.parameter

    match = get_paramdef_for_parameter(path, param_holder, dblink)

    if match and match.rebuild_required:
        validate_rebuild_required(session, path, param_holder.personality_stage)

    if dblink:
        path = Parameter.feature_path(dblink, path)
    parameter.del_path(path)


def del_all_feature_parameter(session, dblink):
    # TODO: if the feature is bound to the whole archetype, then we should clean
    # up all personalities here
    if not dblink or not dblink.personality_stage or \
       not dblink.personality_stage.paramholder or \
       not dblink.feature.param_def_holder:
        return

    parameter = dblink.personality_stage.paramholder.parameter
    dbstage = dblink.personality_stage
    for paramdef in dblink.feature.param_def_holder.param_definitions:
        if paramdef.rebuild_required:
            validate_rebuild_required(session, paramdef.path, dbstage)

        parameter.del_path(Parameter.feature_path(dblink, paramdef.path),
                           compel=False)

def validate_value(label, value_type, value):
    retval = None

    if value_type == 'string' or value_type == 'list':
        retval = value
    elif value_type == 'int':
        retval = force_int(label, value)
    elif value_type == 'float':
        retval = force_float(label, value)
    elif value_type == 'boolean':
        retval = force_boolean(label, value)
    elif value_type == 'json':
        retval = force_json_dict(label, value)

    if retval is None:
        raise ArgumentError("Value %s for path %s has to be of type %s." %
                            (value, label, value_type))

    return retval


def validate_parameter(session, path, value, param_holder, featurelink=None):
    """
        Validates parameter before updating in db.
        - checks if matching parameter definition exists
        - if value is not specified on input if a default value
          has been defined on the definition
        - if rebuild_required validate do validation on host status
    """

    match = get_paramdef_for_parameter(path, param_holder, featurelink)
    if not match:
        raise ArgumentError("Parameter %s does not match any parameter definitions"
                            % path)

    # check if default specified on parameter definition
    if not value:
        if match.default:
            value = match.default
        else:
            raise ArgumentError("Parameter %s does not have any value defined."
                                % path)

    retval = validate_value(path, match.value_type, value)

    if match.rebuild_required:
        validate_rebuild_required(session, path, param_holder.personality_stage)

    return retval


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


def get_paramdef_for_parameter(path, param_holder, dbfeaturelink):
    if dbfeaturelink:
        param_def_holder = dbfeaturelink.feature.param_def_holder
    else:
        param_def_holder = param_holder.archetype.param_def_holder

    if not param_def_holder:
        return None

    param_definitions = param_def_holder.param_definitions
    match = None

    # the specified path of the parameter should either be an actual match
    # or match input specified regexp.
    # The regexp is done only after all actual paths dont find a match
    # e.g action/\w+/user will never be an actual match
    for paramdef in param_definitions:
        if path == paramdef.path:
            match = paramdef
            break

    if not match:
        for paramdef in param_definitions:
            if re.match(paramdef.path + '$', path):
                match = paramdef
                break

    return match


def validate_required_parameter(param_definitions, parameter, dbfeaturelink=None):
    errors = []
    formatter = ParamDefinitionFormatter()
    for param_def in param_definitions:
        # ignore not required fields or fields
        # which have defaults specified
        if (not param_def.required) or param_def.default:
            continue

        if not parameter:
            value = None
        elif dbfeaturelink:
            value = parameter.get_feature_path(dbfeaturelink, param_def.path,
                                               compel=False)
        else:
            value = parameter.get_path(param_def.path, compel=False)

        if value is None:
            errors.append(formatter.format_raw(param_def))

    return errors


def search_path_in_personas(session, path, param_def_holder):
    q = session.query(PersonalityParameter)
    q = q.join(PersonalityStage)
    q = q.options(contains_eager('personality_stage'))
    if isinstance(param_def_holder, ArchetypeParamDef):
        q = q.join(Personality)
        q = q.options(contains_eager('personality_stage.personality'))
        q = q.filter_by(archetype=param_def_holder.archetype)
    else:
        q = q.join(FeatureLink)
        q = q.filter_by(feature=param_def_holder.feature)
    q = q.options(subqueryload('parameter'))

    holder = {}
    trypath = []
    if isinstance(param_def_holder, ArchetypeParamDef):
        trypath.append(path)
    for param_holder in q:
        try:
            if not isinstance(param_def_holder, ArchetypeParamDef):
                trypath = []
                q = session.query(FeatureLink)
                q = q.filter_by(feature=param_def_holder.feature,
                                personality_stage=param_holder.personality_stage)

                for link in q.all():
                    trypath.append(Parameter.feature_path(link, path))

            for tpath in trypath:
                value = param_holder.parameter.get_path(tpath)
                if value is not None:
                    holder[param_holder] = {path: value}
        except NotFoundException:
            pass
    return holder


def validate_personality_config(dbstage):
    """
        Validates all the parameters on personality to validate
        if all required parameters have been set. All feature
        parameters are also validated.
    """
    dbarchetype = dbstage.personality.archetype

    if dbstage.paramholder:
        parameter = dbstage.paramholder.parameter
    else:
        parameter = None

    error = []

    if dbarchetype.param_def_holder:
        param_definitions = dbarchetype.param_def_holder.param_definitions
        error += validate_required_parameter(param_definitions, parameter)

    # features for personalities
    for link in dbarchetype.features + dbstage.features:
        param_definitions = []
        if link.feature.param_def_holder:
            param_definitions = link.feature.param_def_holder.param_definitions
            tmp_error = validate_required_parameter(param_definitions, parameter, link)
            if tmp_error:
                error.append("Feature Binding : %s" % link.feature)
                error += tmp_error
    return error


def validate_param_definition(path, value_type, default=None):
    """
        Over here we are a bit restrictive then panc and do not allow
        underscores as path starters. So far we haven't needed those
        but this restriction can be relaxed in the future if needed.
        Suggestions were to validate each path component to validate
        against valid pan id but we are using regexp in certain cases
        as parameter paths i.e actions so this would not work.
    """

    if not path[0].isalpha():
        raise ArgumentError("Invalid path {0} specified, path cannot start with special characters".format(path))

    ParamDefinition.validate_type(value_type)

    if default:
        validate_value("default for path=%s" % path, value_type, default)

    return path
