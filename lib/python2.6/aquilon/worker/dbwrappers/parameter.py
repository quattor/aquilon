# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.utils import (force_json_dict, force_int, force_float,
                           force_boolean)
from sqlalchemy.sql import or_
from aquilon.aqdb.model import (Personality, Parameter,
                                Feature, FeatureLink, Host,
                                HostLifecycle, Model,
                                ArchetypeParamDef,
                                PersonalityParameter)
from aquilon.worker.formats.parameter_definition import ParamDefinitionFormatter


def get_parameter_holder(session, archetype=None, personality=None,
                         auto_include=False):
    db_param_holder = None
    dbpersonality = None
    if  isinstance(personality, Personality):
        dbpersonality = personality
    else:
        dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
    db_param_holder = dbpersonality.paramholder

    if db_param_holder is None and auto_include:
        db_param_holder = PersonalityParameter(personality=dbpersonality)
        session.add(db_param_holder)

    return db_param_holder


def get_feature_link(session, feature, model, interface_name, personality):
    dblink = None
    dbmodel = None
    feature_type = 'host'
    if interface_name:
        feature_type = 'interface'
    if model:
        feature_type = 'hardware'
        dbmodel = Model.get_unique(session, name=model,
                                   compel=True)

    dbfeature = Feature.get_unique(session, name=feature,
                                   feature_type=feature_type, compel=True)
    dblink = FeatureLink.get_unique(session, feature=dbfeature,
                                    interface_name=interface_name,
                                    model=dbmodel, personality=personality,
                                    compel=True)
    return dblink


def set_parameter(session, param_holder, feature, model, interface_name,
                  path, value, compel=False, preclude=False):
    """
        Handles add parameter as well as update parameter. Parmeters for features
        will be stored as part of personality as features/<feature_name>/<path>
    """

    dbparameter = Parameter.get_unique(session, holder=param_holder,
                                       compel=compel)
    ## create dbparameter if doesnt exist
    if not dbparameter:
        if compel:
            raise NotFoundException("No parameter of path=%s defined." % path)

        dbparameter = Parameter(holder=param_holder, value={})

    dblink = None
    if feature:
        dblink = get_feature_link(session, feature, model, interface_name,
                                  param_holder.personality)

    retval, param_def = validate_parameter(session, path, value, param_holder, dblink)

    if feature:
        path = Parameter.feature_path(dblink, path)
    dbparameter.set_path(path, retval, compel, preclude)
    dbparameter.param_def = param_def
    return dbparameter


def del_parameter(session, path, param_holder, feature=None, model=None, interface_name=None):
    dbparameter = Parameter.get_unique(session, holder=param_holder,
                                       compel=True)

    dblink = None
    if feature:
        dblink = get_feature_link(session, feature, model, interface_name,
                                  param_holder.personality)

    match = get_paramdef_for_parameter(session, path, param_holder, dblink)

    if match and match.rebuild_required:
        validate_rebuild_required(session, path, param_holder)

    if dblink:
        path = Parameter.feature_path(dblink, path)
    dbparameter.del_path(path)
    return dbparameter


def del_all_feature_parameter(session, dblink):

    if not dblink:
        return

    paramdef_holder = None
    param_definitions = None
    if dblink:
        paramdef_holder = dblink.feature.paramdef_holder
        if paramdef_holder:
            param_definitions = paramdef_holder.param_definitions

    if not param_definitions:
        return

    dbparams = get_parameters(session, archetype=None,
                              personality=dblink.personality)

    if not dbparams:
        return

    for paramdef in param_definitions:
        for dbparam in dbparams:
            if paramdef.rebuild_required:
                validate_rebuild_required(session, paramdef.path, dbparam.holder)

            dbparam.del_path(Parameter.feature_path(dblink, paramdef.path),
                             compel=False)

    return


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

    if  retval == None:
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

    match = get_paramdef_for_parameter(session, path, param_holder, featurelink)
    if not match:
        raise ArgumentError("Parameter %s does not match any parameter definitions"
                            % path)

    retval = None

    ## check if default specified on parameter definition
    if not value:
        if match.default:
            value = match.default
        else:
            raise ArgumentError("Parameter %s does not have any value defined."
                                % path)

    retval = validate_value(path, match.value_type, value)

    if match.rebuild_required:
        validate_rebuild_required(session, path, param_holder)

    return retval, match


def validate_rebuild_required(session, path, param_holder):
    """ check if this parameter requires hosts to be in non-ready state
    """
    q = session.query(Host)
    dbready = HostLifecycle.get_unique(session, "ready", compel=True)
    dbalmostready = HostLifecycle.get_unique(session, "almostready", compel=True)
    q = q.filter(or_(Host.status == dbready, Host.status == dbalmostready))
    personality = param_holder.personality
    if isinstance(param_holder, PersonalityParameter):
        q = q.filter_by(personality=personality)
    if q.count():
        raise ArgumentError("Modifying parameter %s value needs a host rebuild. "
                            "There are hosts associated to the personality in non-ready state. "
                            "Please set these host to status of rebuild to continue. "
                            "Run 'aq search host --personality %s --buildstatus ready' "
                            "and 'aq search host --personality %s --buildstatus almostready' to "
                            "get the list of the affected hosts." %
                            (path, personality, personality))


def get_parameters(session, archetype=None, personality=None):

    param_holder = get_parameter_holder(session, archetype=archetype,
                                        personality=personality,
                                        auto_include=False)
    if param_holder is None:
        return []
    q = session.query(Parameter).filter_by(holder=param_holder)
    return q.all()


def get_paramdef_for_parameter(session, path, param_holder, dbfeaturelink=None):
    param_definitions = None
    match = None

    if dbfeaturelink:
        paramdef_holder = dbfeaturelink.feature.paramdef_holder
    else:
        paramdef_holder = param_holder.personality.archetype.paramdef_holder

    if paramdef_holder:
        param_definitions = paramdef_holder.param_definitions
    else:
        param_definitions = []

    ## the specified path of the parameter should either be an actual match
    ## or match input specified regexp.
    ## The regexp is done only after all actual paths dont find a match
    ## e.g action/\w+/user will never be an actual match
    for paramdef in param_definitions:
        if path == paramdef.path:
            match = paramdef

    if not match:
        for paramdef in param_definitions:
            if re.match(paramdef.path + '$', path):
                match = paramdef

    return match


def validate_required_parameter(param_definitions, parameters, dbfeaturelink=None):
    errors = []
    formatter = ParamDefinitionFormatter()
    for param_def in param_definitions:
        ## ignore not required fields or fields
        ## which have defaults specified
        if (not param_def.required) or param_def.default:
            continue

        value = None
        for param in parameters:
            if dbfeaturelink:
                value = param.get_feature_path(dbfeaturelink, param_def.path, compel=False)
            else:
                value = param.get_path(param_def.path, compel=False)
            if value:
                break
            ## ignore if value is specified
        if value is None:
            errors.append(formatter.format_raw(param_def))

    return errors


def search_path_in_personas(session, path, paramdef_holder):

    q = session.query(PersonalityParameter)
    q = q.join(Personality)
    if isinstance(paramdef_holder, ArchetypeParamDef):
        q = q.filter_by(archetype=paramdef_holder.archetype)
    else:
        q = q.join(FeatureLink)
        q = q.filter_by(feature=paramdef_holder.feature)

    holder = {}
    trypath = []
    if isinstance(paramdef_holder, ArchetypeParamDef):
        trypath.append(path)
    for param_holder in q.all():
        try:
            if not isinstance(paramdef_holder, ArchetypeParamDef):
                trypath = []
                q = session.query(FeatureLink)
                q = q.filter_by(feature=paramdef_holder.feature,
                                personality=param_holder.personality)

                for link in q.all():
                    trypath.append(Parameter.feature_path(link, path))

            for tpath in trypath:
                for param in param_holder.parameters:
                    value = param.get_path(tpath)
                    if value:
                        holder[param_holder] = {path: value}
        except NotFoundException:
            pass
    return holder


def validate_personality_config(session, archetype, personality):
    """
        Validates all the parameters on personality to validate
        if all required parameters have been set. All feature
        parameters are also validated.
    """
    dbpersonality = None
    if  isinstance(personality, Personality):
        dbpersonality = personality
    else:
        dbpersonality = Personality.get_unique(session,
                                           name=personality,
                                           archetype=archetype,
                                           compel=True)
    dbarchetype = dbpersonality.archetype

    error = []
    ## validate parameters
    param_definitions = []
    parameters = get_parameters(session, personality=dbpersonality)
    if dbarchetype.paramdef_holder:
        param_definitions = dbarchetype.paramdef_holder.param_definitions
        error += validate_required_parameter(param_definitions, parameters)

    ## features  for personalities
    for link in dbarchetype.features + dbpersonality.features:
        param_definitions = []
        if link.feature.paramdef_holder:
            param_definitions = link.feature.paramdef_holder.param_definitions
            tmp_error = validate_required_parameter(param_definitions, parameters, link)
            if tmp_error:
                error.append("Feature Binding : %s" % link.feature)
                error += tmp_error
    return error
