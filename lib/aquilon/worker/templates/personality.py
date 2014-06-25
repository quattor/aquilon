# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

import logging
from collections import defaultdict

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import object_session

from aquilon.aqdb.model import Personality, Parameter
from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates.base import (Plenary, StructurePlenary,
                                           TemplateFormatter, PlenaryCollection)
from aquilon.worker.templates.panutils import (pan_include, pan_variable,
                                               pan_assign, pan_append,
                                               pan_include_if_exists)
from aquilon.worker.dbwrappers.parameter import (validate_value,
                                                 get_parameters)

LOGGER = logging.getLogger(__name__)


def string_to_list(data):
    return [item.strip() for item in data.split(',') if item]


def get_parameters_by_feature(dbfeaturelink):
    ret = {}
    paramdef_holder = dbfeaturelink.feature.paramdef_holder
    if not paramdef_holder:
        return ret

    param_definitions = paramdef_holder.param_definitions
    parameters = get_parameters(object_session(dbfeaturelink),
                                personality=dbfeaturelink.personality)

    for param_def in param_definitions:
        value = None
        for param in parameters:
            value = param.get_feature_path(dbfeaturelink,
                                           param_def.path, compel=False)
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
        pan_assign(lines, "/system/%s/%s" % (dbfeaturelink.cfg_path_escaped, path), params[path])
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
                # coerce string list to list
                if param_def.value_type == 'list':
                    value = string_to_list(value)

                get_path_under_top(param_def.path, value,
                                   ret[param_def.template])

        # if all parameters are not defined still generate empty template
        if param_def.template not in ret:
            ret[param_def.template] = defaultdict()
    return ret


# Normally we have exactly one instance of every plenary class per DB object.
# This class just wraps the (personality, template path) tuple to make parameter
# plenaries behave the same way.
class ParameterTemplate(object):
    def __init__(self, dbpersonality, template, values):
        self.personality = dbpersonality
        self.template = template
        self.values = values

    def __str__(self):
        return "%s/%s" % (self.personality.name, self.template)


class PlenaryPersonality(PlenaryCollection):

    def __init__(self, dbpersonality, logger=LOGGER):
        super(PlenaryPersonality, self).__init__(logger=logger)

        self.dbobj = dbpersonality

        self.plenaries.append(PlenaryPersonalityBase.get_plenary(dbpersonality))
        self.plenaries.append(PlenaryPersonalityPreFeature.get_plenary(dbpersonality))
        self.plenaries.append(PlenaryPersonalityPostFeature.get_plenary(dbpersonality))

        # mulitple structure templates for parameters
        for path, values in get_parameters_by_tmpl(dbpersonality).items():
            ptmpl = ParameterTemplate(dbpersonality, path, values)
            self.plenaries.append(PlenaryPersonalityParameter.get_plenary(ptmpl))

        self.name = dbpersonality.name

    def get_key(self, exclusive=True):
        if inspect(self.dbobj).deleted:
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj, logger=self.logger,
                              exclusive=exclusive)

Plenary.handlers[Personality] = PlenaryPersonality


class FeatureTemplate(TemplateFormatter):
    template_raw = "feature.mako"


class PlenaryPersonalityBase(Plenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbpersonality):
        return "%s/%s/config" % (cls.prefix, dbpersonality.name)

    @classmethod
    def loadpath(cls, dbpersonality):
        return dbpersonality.archetype.name

    def body(self, lines):
        pan_variable(lines, "PERSONALITY", self.dbobj.name)

        # process grns
        eon_id_map = defaultdict(set)

        # own == pers level
        for grn_rec in self.dbobj._grns:
            eon_id_map[grn_rec.target].add(grn_rec.grn.eon_id)

        for target, eon_id_set in eon_id_map.iteritems():
            for eon_id in sorted(eon_id_set):
                pan_append(lines, "/system/eon_id_maps/%s" % target, eon_id)

        section = "archetype_" + self.dbobj.archetype.name
        # backward compat for esp reporting
        if self.config.has_option(section, "default_grn_target"):
            default_grn_target = self.config.get(section, "default_grn_target")

            for eon_id in sorted(eon_id_map[default_grn_target]):
                pan_append(lines, "/system/eon_ids", eon_id)

        pan_assign(lines, "/system/personality/owner_eon_id",
                   self.dbobj.owner_eon_id)

        user_list = sorted(dbusr.name for dbusr in self.dbobj.root_users)
        if user_list:
            pan_assign(lines, "/system/root_users", user_list)

        ng_list = sorted(str(ng) for ng in self.dbobj.root_netgroups)
        if ng_list:
            pan_assign(lines, "/system/root_netgroups", ng_list)

        # include pre features
        path = PlenaryPersonalityPreFeature.template_name(self.dbobj)
        pan_include_if_exists(lines, path)

        # process parameter templates
        pan_include_if_exists(lines, "personality/config")
        pan_assign(lines, "/system/personality/name", self.dbobj.name)
        if self.dbobj.host_environment.name != 'legacy':
            pan_assign(lines, "/system/personality/host_environment",
                       self.dbobj.host_environment, True)

        # TODO: This is just to satisfy quattor schema
        # needs to be removed as soon as the schema allows this
        pan_assign(lines, "/system/personality/systemgrn", [])

        if self.dbobj.config_override:
            pan_include(lines, "features/personality/config_override/config")

        # include post features
        path = PlenaryPersonalityPostFeature.template_name(self.dbobj)
        pan_include_if_exists(lines, path)


class PlenaryPersonalityPreFeature(Plenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbpersonality):
        return "%s/%s/pre_feature" % (cls.prefix, dbpersonality)

    @classmethod
    def loadpath(cls, dbpersonality):
        return dbpersonality.archetype.name

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

        # hardware features should precede host features
        for link in model_feat + interface_feat + pre_feat:
            helper_feature_template(feat_tmpl, link, lines)


class PlenaryPersonalityPostFeature(Plenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbpersonality):
        return "%s/%s/post_feature" % (cls.prefix, dbpersonality)

    @classmethod
    def loadpath(cls, dbpersonality):
        return dbpersonality.archetype.name

    def body(self, lines):
        feat_tmpl = FeatureTemplate()
        for link in self.dbobj.archetype.features + self.dbobj.features:
            if link.feature.post_personality:
                helper_feature_template(feat_tmpl, link, lines)


class PlenaryPersonalityParameter(StructurePlenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, ptmpl):
        return "%s/%s/%s" % (cls.prefix, ptmpl.personality.name, ptmpl.template)

    @classmethod
    def loadpath(cls, ptmpl):
        return ptmpl.personality.archetype.name

    def __init__(self, ptmpl, logger=LOGGER):
        super(PlenaryPersonalityParameter, self).__init__(ptmpl,
                                                          logger=logger)
        self.parameters = ptmpl.values

    def body(self, lines):
        for path in self.parameters:
            pan_assign(lines, path, self.parameters[path])
