# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
from six import iteritems

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import object_session

from aquilon.aqdb.model import PersonalityStage, Parameter
from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates.base import (Plenary, StructurePlenary,
                                           TemplateFormatter, PlenaryCollection)
from aquilon.worker.templates.panutils import (pan_include, pan_variable,
                                               pan_assign, pan_append,
                                               pan_include_if_exists)
from aquilon.worker.dbwrappers.parameter import validate_value

LOGGER = logging.getLogger(__name__)


def string_to_list(data):
    return [item.strip() for item in data.split(',') if item]


def get_parameters_by_feature(dbstage, dbfeaturelink):
    ret = {}
    paramdef_holder = dbfeaturelink.feature.paramdef_holder
    if not paramdef_holder or not dbstage.paramholder:
        return ret

    parameters = dbstage.paramholder.parameters
    for param_def in paramdef_holder.param_definitions:
        for param in parameters:
            value = param.get_feature_path(dbfeaturelink,
                                           param_def.path, compel=False)
            if value is None and param_def.default:
                value = validate_value("default for path=%s" % param_def.path,
                                       param_def.value_type, param_def.default)
            if value is not None:
                if param_def.value_type == 'list':
                    value = string_to_list(value)
                ret[param_def.path] = value
    return ret


def helper_feature_template(dbstage, featuretemplate, dbfeaturelink, lines):
    params = get_parameters_by_feature(dbstage, dbfeaturelink)
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


def get_parameters_by_tmpl(dbstage):
    ret = defaultdict(dict)

    dbpersonality = dbstage.personality
    paramdef_holder = dbpersonality.archetype.paramdef_holder
    if not paramdef_holder:
        return ret

    if dbstage.paramholder:
        parameters = dbstage.paramholder.parameters
    else:
        parameters = []

    for param_def in paramdef_holder.param_definitions:
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


def staged_path(prefix, dbstage, suffix):
    if dbstage.name == "current":
        return "%s/%s/%s" % (prefix, dbstage.personality.name, suffix)
    else:
        return "%s/%s+%s/%s" % (prefix, dbstage.personality.name,
                                dbstage.name, suffix)


# Normally we have exactly one instance of every plenary class per DB object.
# This class just wraps the (personality, template path) tuple to make parameter
# plenaries behave the same way.
class ParameterTemplate(object):
    def __init__(self, dbstage, template, values):
        self.personality_stage = dbstage
        self.template = template
        self.values = values

    def __str__(self):
        return "%s/%s" % (self.personality_stage.personality.name,
                          self.template)


class PlenaryPersonality(PlenaryCollection):

    def __init__(self, dbstage, logger=LOGGER, allow_incomplete=True):
        super(PlenaryPersonality, self).__init__(logger=logger,
                                                 allow_incomplete=allow_incomplete)

        self.dbobj = dbstage

        self.append(PlenaryPersonalityBase.get_plenary(dbstage,
                                                       allow_incomplete=allow_incomplete))
        self.append(PlenaryPersonalityPreFeature.get_plenary(dbstage,
                                                             allow_incomplete=allow_incomplete))
        self.append(PlenaryPersonalityPostFeature.get_plenary(dbstage,
                                                              allow_incomplete=allow_incomplete))

        # mulitple structure templates for parameters
        for path, values in get_parameters_by_tmpl(dbstage).items():
            ptmpl = ParameterTemplate(dbstage, path, values)
            self.append(PlenaryPersonalityParameter.get_plenary(ptmpl,
                                                                allow_incomplete=allow_incomplete))

    def get_key(self, exclusive=True):
        if inspect(self.dbobj).deleted:
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj, logger=self.logger,
                              exclusive=exclusive)

Plenary.handlers[PersonalityStage] = PlenaryPersonality


class FeatureTemplate(TemplateFormatter):
    template_raw = "feature.mako"


class PlenaryPersonalityBase(Plenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbstage):
        return staged_path(cls.prefix, dbstage, "config")

    @classmethod
    def loadpath(cls, dbstage):
        return dbstage.personality.archetype.name

    def body(self, lines):
        dbpers = self.dbobj.personality

        if self.dbobj.name == "current":
            pan_variable(lines, "PERSONALITY", dbpers.name)
        else:
            pan_variable(lines, "PERSONALITY", "%s+%s" % (dbpers.name,
                                                          self.dbobj.name))

        # process grns
        eon_id_map = defaultdict(set)

        # own == pers level
        for grn_rec in self.dbobj.grns:
            eon_id_map[grn_rec.target].add(grn_rec.grn.eon_id)

        for target, eon_id_set in iteritems(eon_id_map):
            for eon_id in sorted(eon_id_set):
                pan_append(lines, "/system/eon_id_maps/%s" % target, eon_id)

        section = "archetype_" + dbpers.archetype.name
        # backward compat for esp reporting
        if self.config.has_option(section, "default_grn_target"):
            default_grn_target = self.config.get(section, "default_grn_target")

            for eon_id in sorted(eon_id_map[default_grn_target]):
                pan_append(lines, "/system/eon_ids", eon_id)

        pan_assign(lines, "/system/personality/owner_eon_id",
                   dbpers.owner_eon_id)

        user_list = sorted(dbusr.name for dbusr in dbpers.root_users)
        if user_list:
            pan_assign(lines, "/system/root_users", user_list)

        ng_list = sorted(str(ng) for ng in dbpers.root_netgroups)
        if ng_list:
            pan_assign(lines, "/system/root_netgroups", ng_list)

        # include pre features
        path = PlenaryPersonalityPreFeature.template_name(self.dbobj)
        pan_include_if_exists(lines, path)

        # process parameter templates
        pan_include_if_exists(lines, "personality/config")
        pan_assign(lines, "/system/personality/name", dbpers.name)
        if dbpers.host_environment.name != 'legacy':
            pan_assign(lines, "/system/personality/host_environment",
                       dbpers.host_environment, True)

        if dbpers.config_override:
            pan_include(lines, "features/personality/config_override/config")

        # include post features
        path = PlenaryPersonalityPostFeature.template_name(self.dbobj)
        pan_include_if_exists(lines, path)


class PlenaryPersonalityPreFeature(Plenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbstage):
        return staged_path(cls.prefix, dbstage, "pre_feature")

    @classmethod
    def loadpath(cls, dbstage):
        return dbstage.personality.archetype.name

    def body(self, lines):
        feat_tmpl = FeatureTemplate()
        model_feat = []
        interface_feat = []
        pre_feat = []
        dbpers = self.dbobj.personality
        for link in dbpers.archetype.features + self.dbobj.features:
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
            helper_feature_template(self.dbobj, feat_tmpl, link, lines)


class PlenaryPersonalityPostFeature(Plenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbstage):
        return staged_path(cls.prefix, dbstage, "post_feature")

    @classmethod
    def loadpath(cls, dbstage):
        return dbstage.personality.archetype.name

    def body(self, lines):
        feat_tmpl = FeatureTemplate()
        dbpers = self.dbobj.personality
        for link in dbpers.archetype.features + self.dbobj.features:
            if link.feature.post_personality:
                helper_feature_template(self.dbobj, feat_tmpl, link, lines)


class PlenaryPersonalityParameter(StructurePlenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, ptmpl):
        return staged_path(cls.prefix, ptmpl.personality_stage, ptmpl.template)

    @classmethod
    def loadpath(cls, ptmpl):
        return ptmpl.personality_stage.personality.archetype.name

    def __init__(self, ptmpl, **kwargs):
        super(PlenaryPersonalityParameter, self).__init__(ptmpl, **kwargs)
        self.parameters = ptmpl.values

    def body(self, lines):
        for path in self.parameters:
            pan_assign(lines, path, self.parameters[path])

    def is_deleted(self):
        dbobj = self.dbobj.personality_stage
        session = object_session(dbobj)
        return dbobj in session.deleted or inspect(dbobj).deleted

    def is_dirty(self):
        session = object_session(self.dbobj.personality_stage)
        return self.dbobj.personality_stage in session.dirty
