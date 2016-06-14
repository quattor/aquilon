# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
from sqlalchemy.orm import joinedload, subqueryload

from aquilon.aqdb.model import PersonalityStage, PersonalityParameter
from aquilon.aqdb.model.feature import host_features
from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates.base import (Plenary, StructurePlenary,
                                           PlenaryCollection)
from aquilon.worker.templates.panutils import (pan_include, pan_variable,
                                               pan_assign, pan_append,
                                               pan_include_if_exists)

LOGGER = logging.getLogger(__name__)


def get_parameters_by_feature(dbstage, dbfeature):
    param_def_holder = dbfeature.param_def_holder
    assert param_def_holder

    param = dbstage.parameters.get(param_def_holder, None)

    ret = {}
    for param_def in param_def_holder.param_definitions:
        if param:
            value = param.get_path(param_def.path, compel=False)
        else:
            value = None

        if value is None:
            value = param_def.parsed_default

        if value is not None:
            ret[param_def.path] = value
    return ret


def staged_path(prefix, dbstage, suffix):
    if dbstage.name == "current":
        return "%s/%s/%s" % (prefix, dbstage.personality.name, suffix)
    else:
        return "%s/%s+%s/%s" % (prefix, dbstage.personality.name,
                                dbstage.name, suffix)


class PlenaryPersonality(PlenaryCollection):

    def __init__(self, dbstage, logger=LOGGER, allow_incomplete=True):
        super(PlenaryPersonality, self).__init__(logger=logger,
                                                 allow_incomplete=allow_incomplete)

        self.dbobj = dbstage

        self.append(PlenaryPersonalityBase.get_plenary(dbstage,
                                                       allow_incomplete=allow_incomplete))

        for template, defholder in dbstage.archetype.param_def_holders.items():
            if defholder not in dbstage.parameters:
                logger.client_info("{0} does not have parameters for "
                                   "template {1!s}.".format(dbstage, template))
                continue

            plenary = PlenaryPersonalityParameter.get_plenary(dbstage.parameters[defholder],
                                                              allow_incomplete=allow_incomplete)
            self.append(plenary)

    def get_key(self, exclusive=True):
        if inspect(self.dbobj).deleted:
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj, logger=self.logger,
                              exclusive=exclusive)

    @classmethod
    def query_options(cls, prefix="", load_personality=True):
        options = []
        if load_personality:
            options.append(joinedload(prefix + 'personality'))
        return options + [subqueryload(prefix + 'parameters'),
                          subqueryload(prefix + 'features'),
                          subqueryload(prefix + 'grns'),
                          joinedload(prefix + 'features.feature'),
                          joinedload(prefix + 'features.feature.param_def_holder'),
                          subqueryload(prefix + 'features.feature.param_def_holder.param_definitions'),
                          joinedload(prefix + 'features.model')]

Plenary.handlers[PersonalityStage] = PlenaryPersonality


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

        pan_assign(lines, "/system/personality/name", dbpers.name)
        if dbpers.staged:
            pan_assign(lines, "/system/personality/stage", self.dbobj.name)

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

        pre, post = host_features(self.dbobj)

        # Only features which are
        # - bound to the personality directly rather than to the archetype,
        # - and have parameter definitions
        # are interesting when generating parameters
        param_features = set(link.feature for link in self.dbobj.features
                             if link.feature.param_def_holder)

        for dbfeature in sorted(frozenset()
                                .union(pre)
                                .union(post)
                                .intersection(param_features),
                                key=attrgetter('name')):
            base_path = "/system/" + dbfeature.cfg_path
            params = get_parameters_by_feature(self.dbobj, dbfeature)

            for key in sorted(params.keys()):
                pan_assign(lines, base_path + "/" + key, params[key])

        for dbfeature in sorted(pre, key=attrgetter('name')):
            pan_include(lines, dbfeature.cfg_path + "/config")
            pan_append(lines, "/metadata/features", dbfeature.cfg_path + "/config")

        pan_include_if_exists(lines, "personality/config")

        if dbpers.host_environment.name != 'legacy':
            pan_assign(lines, "/system/personality/host_environment",
                       dbpers.host_environment, True)

        if dbpers.config_override:
            pan_include(lines, "features/personality/config_override/config")

        for dbfeature in sorted(post, key=attrgetter('name')):
            pan_include(lines, dbfeature.cfg_path + "/config")
            pan_append(lines, "/metadata/features", dbfeature.cfg_path + "/config")

    def get_key(self, exclusive=True):
        if self.is_deleted():
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj, logger=self.logger,
                              exclusive=exclusive)


class PlenaryPersonalityParameter(StructurePlenary):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbparam):
        return staged_path(cls.prefix, dbparam.personality_stage,
                           dbparam.param_def_holder.template)

    @classmethod
    def loadpath(cls, dbparam):
        return dbparam.personality_stage.personality.archetype.name

    def __init__(self, *args, **kwargs):
        super(PlenaryPersonalityParameter, self).__init__(*args, **kwargs)
        self.debug_name = "%s/%s" % (self.dbobj.personality_stage.qualified_name,
                                     self.dbobj.param_def_holder.template)

    def body(self, lines):
        dbparam = self.dbobj
        param_def_holder = dbparam.param_def_holder

        for param_def in sorted(param_def_holder.param_definitions,
                                key=attrgetter('path')):
            value = dbparam.get_path(param_def.path, compel=False)

            if value is None:
                value = param_def.parsed_default

            if value is None:
                continue

            # Do a single-level expansion of JSON parameters. This should be
            # more efficient to compile according to the Pan documentation, and
            # it also avoids trying to assign a value to an empty path if a
            # single parameter definition covers the whole template
            if isinstance(value, dict):
                for k in sorted(value):
                    v = value[k]

                    if param_def.path:
                        pan_assign(lines, param_def.path + "/" + k, v)
                    else:
                        pan_assign(lines, k, v)
            else:
                pan_assign(lines, param_def.path, value)

    def get_key(self, exclusive=True):
        if self.is_deleted():
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(personality=self.dbobj.personality_stage,
                              logger=self.logger, exclusive=exclusive)

Plenary.handlers[PersonalityParameter] = PlenaryPersonalityParameter
