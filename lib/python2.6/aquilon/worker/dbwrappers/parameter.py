# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" Helper functions for managing parameters. """

import re
from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.utils import (force_json_dict, force_int, force_float,
                           force_boolean)

from sqlalchemy.sql import or_
from aquilon.aqdb.model import (Archetype, Personality, Parameter,
                                Feature, FeatureLink, Host,
                                HostLifecycle,
                                PersonalityParameter,
                                FeatureLinkParameter)


def get_parameter_holder(session, archetype=None, personality=None,
                         feature=None, featurelink=None, auto_include=False):
    db_param_holder = None
    dbpersonality = None
    dbfeaturelink = None
    if personality:
        if  isinstance(personality, Personality):
            dbpersonality = personality
        else:
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
        db_param_holder = dbpersonality.paramholder

    if featurelink:
        dbfeaturelink = featurelink
        db_param_holder = dbfeaturelink.paramholder
    elif feature:
        if isinstance(feature, Feature):
            dbfeature = feature
        else:
            dbfeature = Feature.get_unique(session, name=feature, compel=True)
        q = session.query(FeatureLink)
        q = q.filter_by(feature=dbfeature)
        if dbpersonality:
            q = q.filter_by(personality=dbpersonality)
        elif archetype:
            dbarch = Archetype.get_unique(session, name=archetype, compel=True)
            q = q.filter_by(archetype=dbarch)

        dbfeaturelink = q.first()
        if not dbfeaturelink:
            raise NotFoundException("No feature binding found for {0:l}."
                                    .format(dbfeature))
        db_param_holder = dbfeaturelink.paramholder

    if db_param_holder is None and auto_include:
        if dbfeaturelink:
            db_param_holder = FeatureLinkParameter(featurelink=dbfeaturelink)
        elif dbpersonality:
            db_param_holder = PersonalityParameter(personality=dbpersonality)
    if db_param_holder and auto_include:
        session.add(db_param_holder)

    return db_param_holder


def set_parameter(session, param_holder, path, value, compel=False,
                  preclude=False):
    """ handles add parameter as well as update parameter
    """

    dbparameter = Parameter.get_unique(session, holder=param_holder,
                                       compel=compel)

    ## create dbparameter if doesnt exist
    if not dbparameter:
        if compel:
            raise NotFoundException("No parameter of path=%s defined." % path)

        dbparameter = Parameter(holder=param_holder, value={})

    retval, param_def = validate_parameter(session, path, value, param_holder)
    dbparameter.set_path(path, retval, compel, preclude)
    dbparameter.param_def = param_def
    return dbparameter


def del_parameter(session, path, param_holder):
    dbparameter = Parameter.get_unique(session, holder=param_holder,
                                       compel=True)

    match = get_paramdef_for_parameter(path, param_holder)

    if match and match.rebuild_required:
        validate_rebuild_required(session, path, param_holder)

    dbparameter.del_path(path)
    return dbparameter


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


def validate_parameter(session, path, value, param_holder):
    match = get_paramdef_for_parameter(path, param_holder)
    if not match:
        raise ArgumentError("Parameter %s does not match any parameter "
                            "definitions for the archetype." % path)

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

def validate_rebuild_required (session, path, param_holder):
    """ check if this parameter requires hosts to be in non-ready state
    """
    q = session.query(Host)
    dbready = HostLifecycle.get_unique(session, "ready", compel=True)
    dbalmostready = HostLifecycle.get_unique(session, "almostready", compel=True)
    q = q.filter(or_(Host.status == dbready, Host.status == dbalmostready))
    personality = ""
    if isinstance(param_holder, PersonalityParameter):
        personality = param_holder.personality
    else:
        personality = param_holder.featurelink.personality

    q = q.filter_by(personality=personality)
    if q.count():
        raise ArgumentError("Modifying parameter %s value needs a host rebuild. "
                            "There are hosts associated to the personality in non-ready state. "
                            "Please set these host to status of rebuild to continue. "
                            "Run 'aq search host --personality %s --buildstatus ready' "
                            "and 'aq search host --personality %s --buildstatus almostready' to "
                            "get the list of the affected hosts." %
                            (path, personality, personality)  )

def get_parameters(session, archetype=None, personality=None, feature=None,
                   featurelink=None):

    param_holder = get_parameter_holder(session, archetype=archetype,
                                        personality=personality,
                                        feature=feature,
                                        featurelink=featurelink,
                                        auto_include=False)
    if param_holder is None:
        return []
    q = session.query(Parameter).filter_by(holder=param_holder)
    return q.all()

def get_paramdef_for_parameter(path, param_holder):
    param_definitions = None
    match = None

    if isinstance(param_holder, PersonalityParameter):
        paramdef_holder = param_holder.personality.archetype.paramdef_holder
    else:
        paramdef_holder = param_holder.featurelink.feature.paramdef_holder

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
