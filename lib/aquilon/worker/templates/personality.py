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
from operator import attrgetter
from six import iteritems

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import object_session

from aquilon.aqdb.model import PersonalityStage, ParamDefinition
from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates.base import (Plenary, StructurePlenary,
                                           TemplateFormatter, PlenaryCollection)
from aquilon.worker.templates.panutils import (pan_include, pan_variable,
                                               pan_assign, pan_append,
                                               pan_include_if_exists)

LOGGER = logging.getLogger(__name__)


def get_parameters_by_feature(dbstage, dbfeaturelink):
    ret = {}
    param_def_holder = dbfeaturelink.feature.param_def_holder
    if not param_def_holder or not dbstage.parameter:
        return ret

    parameters = [dbstage.parameter]
    for param_def in param_def_holder.param_definitions:
        for param in parameters:
            if param:
                value = param.get_feature_path(dbfeaturelink.feature,
                                               param_def.path, compel=False)
            else:
                value = None

            if value is None:
                value = param_def.parsed_default

            if value is not None:
                ret[param_def.path] = value
    return ret


def helper_feature_template(dbstage, featuretemplate, dbfeaturelink, lines):
    dbfeature = dbfeaturelink.feature
    params = get_parameters_by_feature(dbstage, dbfeaturelink)
    base_path = "/system/" + dbfeature.cfg_path

    for path in sorted(params.keys()):
        pan_assign(lines, base_path + "/" + path, params[path])

    lines.append(featuretemplate.format_raw(dbfeaturelink))


def get_path_under_top(path, value):
    """ input variable of type xx/yy would be printed as yy only in the
        particular structure template
        if path is just xx and points to a dict
            i.e action = {startup: {a: b}}
            then print as action/startup = pancized({a: b}
        if path is just xx and points to non dict
            ie xx = yy
            then print xx = yy
    """
    ret = {}
    pparts = ParamDefinition.split_path(path)
    if not pparts:
        return ret
    top = pparts.pop(0)
    if pparts:
        ret["/".join(pparts)] = value
    elif isinstance(value, dict):
        for k in value:
            ret[k] = value[k]
    else:
        ret[top] = value
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
    def __init__(self, dbstage, param_def_holder):
        self.personality_stage = dbstage
        self.param_def_holder = param_def_holder

    def __str__(self):
        return "%s/%s" % (self.personality_stage.personality.name,
                          self.param_def_holder.template)


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
        for defholder in dbstage.archetype.param_def_holders.values():
            ptmpl = ParameterTemplate(dbstage, defholder)
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

        pan_assign(lines, "/system/personality/owner_eon_id",
                   dbpers.owner_eon_id)

        user_list = sorted(dbusr.name for dbusr in dbpers.root_users)
        if user_list:
            pan_assign(lines, "/system/root_users", user_list)

        ng_list = sorted(ng.name for ng in dbpers.root_netgroups)
        if ng_list:
            pan_assign(lines, "/system/root_netgroups", ng_list)

        # include pre features
        path = PlenaryPersonalityPreFeature.template_name(self.dbobj)
        pan_include_if_exists(lines, path)

        # process parameter templates
        pan_include_if_exists(lines, "personality/config")
        pan_assign(lines, "/system/personality/name", dbpers.name)
        if dbpers.staged:
            pan_assign(lines, "/system/personality/stage", self.dbobj.name)
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
        for link in sorted(model_feat + interface_feat + pre_feat,
                           key=attrgetter("feature.name")):
            helper_feature_template(self.dbobj, feat_tmpl, link, lines)

    def get_key(self, exclusive=True):
        if self.is_deleted():
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj, logger=self.logger,
                              exclusive=exclusive)


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
        for link in sorted(dbpers.archetype.features + self.dbobj.features,
                           key=attrgetter("feature.name")):
            if link.feature.post_personality:
                helper_feature_template(self.dbobj, feat_tmpl, link, lines)

    def get_key(self, exclusive=True):
        if self.is_deleted():
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj, logger=self.logger,
                              exclusive=exclusive)


class PlenaryPersonalityParameter(StructurePlenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, ptmpl):
        return staged_path(cls.prefix, ptmpl.personality_stage,
                           ptmpl.param_def_holder.template)

    @classmethod
    def loadpath(cls, ptmpl):
        return ptmpl.personality_stage.personality.archetype.name

    def body(self, lines):
        dbstage = self.dbobj.personality_stage
        param_def_holder = self.dbobj.param_def_holder

        if dbstage.parameter:
            parameters = [dbstage.parameter]
        else:
            parameters = []

        for param_def in sorted(param_def_holder.param_definitions,
                                key=attrgetter('path')):
            value = None

            for param in parameters:
                value = param.get_path(param_def.path, compel=False)
                if value is not None:
                    break

            if value is None:
                value = param_def.parsed_default

            if value is not None:
                values = get_path_under_top(param_def.path, value)
                for path in sorted(values.keys()):
                    pan_assign(lines, path, values[path])

    def is_deleted(self):
        for dbobj in (self.dbobj.personality_stage,
                      self.dbobj.param_def_holder):
            session = object_session(dbobj)
            if dbobj in session.deleted or inspect(dbobj).deleted:
                return True

        return False

    def is_dirty(self):
        session = object_session(self.dbobj.personality_stage)
        return self.dbobj.personality_stage in session.dirty

    def get_key(self, exclusive=True):
        if self.is_deleted():
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj.personality_stage,
                              logger=self.logger, exclusive=exclusive)
