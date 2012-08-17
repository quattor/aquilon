# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

import logging

from aquilon.aqdb.model import Personality, Parameter
from aquilon.worker.templates.base import (Plenary, TemplateFormatter,
                                           PlenaryCollection)
from aquilon.worker.templates.panutils import (pan_include,
                                               pan_variable,
                                               pan_assign, pan_push,
                                               pan_include_if_exists)
from aquilon.worker.dbwrappers.parameter import (validate_value,
                                                 get_parameters)
from sqlalchemy.orm import object_session
from collections import defaultdict

LOGGER = logging.getLogger(__name__)


def string_to_list(data):
    ret = []
    for val in data.split(','):
        if isinstance(val, str):
            val = val.strip()
        ret.append(val)
    return ret


def get_parameters_by_feature(dbfeaturelink):
    ret = {}
    paramdef_holder = dbfeaturelink.feature.paramdef_holder
    if not paramdef_holder:
        return ret

    param_definitions = paramdef_holder.param_definitions
    parameters = get_parameters(object_session(dbfeaturelink),
                                featurelink=dbfeaturelink)

    for param_def in param_definitions:
        value = None
        for param in parameters:
            value = param.get_path(param_def.path, compel=False)
            if not value and param_def.default:
                value = validate_value("default for path=%s" % param_def.path,
                                       param_def.value_type, param_def.default)
            if value is not None:
                if param_def.value_type == 'list':
                    value = string_to_list(value)
                ret[param_def.path] = value
    return ret


def helper_feature_template(featuretemplate, dbfeaturelink, lines):

    params = get_parameters_by_feature(dbfeaturelink)
    for path in params:
        pan_variable(lines, path, params[path])
    lines.append(featuretemplate.format_raw(dbfeaturelink))


def get_path_under_top(path, value, ret):
    """ input variable of type xx/yy would be printed as yy only in the
        particular structure template
        if path is just xx and points to a dict
            i.e action = {startup: {a: b}}
            then print as action/startup = pancized({a: b}
        if path is just xx and points to non dict
            ie xx = yy
            then print xx = yy
    """
    pparts = Parameter.path_parts(path)
    if not pparts:
        return
    top = pparts.pop(0)
    if pparts:
        ret[Parameter.topath(pparts)] = value
    elif isinstance(value, dict):
        for k in value:
            ret[k] = value[k]
    else:
        ret[top] = value


def get_parameters_by_tmpl(dbpersonality):
    ret = defaultdict(dict)

    session = object_session(dbpersonality)
    paramdef_holder = dbpersonality.archetype.paramdef_holder
    if not paramdef_holder:
        return ret

    param_definitions = paramdef_holder.param_definitions
    parameters = get_parameters(session, personality=dbpersonality)

    for param_def in param_definitions:
        value = None
        for param in parameters:
            value = param.get_path(param_def.path, compel=False)
            if (value is None) and param_def.default:
                value = validate_value("default for path=%s" % param_def.path,
                                       param_def.value_type, param_def.default)
            if value is not None:
                ## coerce string list to list
                if param_def.value_type == 'list':
                    value = string_to_list(value)

                get_path_under_top(param_def.path, value,
                                   ret[param_def.template])

        ## if all parameters are not defined still generate empty template
        if param_def.template not in ret:
            ret[param_def.template] = defaultdict()
    return ret


class PlenaryPersonality(PlenaryCollection):

    template_type = ""

    def __init__(self, dbpersonality, logger=LOGGER):
        super(PlenaryPersonality, self).__init__(logger=logger)

        self.dbobj = dbpersonality

        self.plenaries.append(PlenaryPersonalityBase(dbpersonality,
                                                     logger=logger))
        self.plenaries.append(PlenaryPersonalityPreFeature(dbpersonality,
                                                           logger=logger))
        self.plenaries.append(PlenaryPersonalityPostFeature(dbpersonality,
                                                            logger=logger))

        ## mulitple structure templates for parameters
        for path, values in get_parameters_by_tmpl(dbpersonality).items():
            plenary = PlenaryPersonalityParameter(dbpersonality, path, values,
                                                  logger=logger)
            self.plenaries.append(plenary)

Plenary.handlers[Personality] = PlenaryPersonality


class FeatureTemplate(TemplateFormatter):
    template_raw = "feature.mako"


class PlenaryPersonalityBase(Plenary):

    template_type = ''

    def __init__(self, dbpersonality, logger=LOGGER):
        super(PlenaryPersonalityBase, self).__init__(dbpersonality,
                                                     logger=logger)

        self.name = dbpersonality.name
        self.loadpath = dbpersonality.archetype.name

        self.plenary_core = "personality/%s" % self.name
        self.plenary_template = "config"

    def body(self, lines):
        pan_variable(lines, "PERSONALITY", self.name)

        ## process grns
        eon_id_list = [grn.eon_id for grn in self.dbobj.grns]
        eon_id_list.sort()
        for eon_id in eon_id_list:
            pan_push(lines, "/system/eon_ids", eon_id)

        ## include pre features
        pan_include_if_exists(lines, "%s/pre_feature" % self.plenary_core)
        ## process parameter templates
        pan_include_if_exists(lines, "personality/config")

        if self.dbobj.config_override:
            pan_include(lines, "features/personality/config_override/config")

        ## include post features
        pan_include_if_exists(lines, "%s/post_feature" % self.plenary_core)


class PlenaryPersonalityPreFeature(Plenary):

    template_type = ""

    def __init__(self, dbpersonality, logger=LOGGER):
        super(PlenaryPersonalityPreFeature, self).__init__(dbpersonality,
                                                           logger=logger)
        self.loadpath = dbpersonality.archetype.name
        self.plenary_core = "personality/%s" % dbpersonality.name
        self.plenary_template = "pre_feature"

    def body(self, lines):
        feat_tmpl = FeatureTemplate()
        model_feat = []
        interface_feat = []
        pre_feat = []
        for link in self.dbobj.archetype.features + self.dbobj.features:
            if link.model:
                model_feat.append(link)
                continue
            if link.interface_name:
                interface_feat.append(link)
                continue
            if not link.feature.post_personality:
                pre_feat.append(link)

        ## hardware features should precede host features
        for link in model_feat + interface_feat + pre_feat:
            helper_feature_template(feat_tmpl, link, lines)


class PlenaryPersonalityPostFeature(Plenary):

    template_type = ""

    def __init__(self, dbpersonality, logger=LOGGER):
        super(PlenaryPersonalityPostFeature, self).__init__(dbpersonality,
                                                            logger=logger)
        self.loadpath = dbpersonality.archetype.name
        self.plenary_core = "personality/%s" % dbpersonality.name
        self.plenary_template = "post_feature"

    def body(self, lines):
        feat_tmpl = FeatureTemplate()
        for link in self.dbobj.archetype.features + self.dbobj.features:
            if link.feature.post_personality:
                helper_feature_template(feat_tmpl, link, lines)


class PlenaryPersonalityParameter(Plenary):

    template_type = "structure"

    def __init__(self, dbpersonality, template, parameters, logger=LOGGER):
        super(PlenaryPersonalityParameter, self).__init__(dbpersonality,
                                                          logger=logger)
        self.loadpath = dbpersonality.archetype.name
        self.plenary_core = "personality/%s" % dbpersonality.name
        self.plenary_template = template

        self.parameters = parameters

    def body(self, lines):
        for path in self.parameters:
            pan_assign(lines, path, self.parameters[path])
