# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2016,2018  Contributor
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

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.aqdb.model import (
    ArchetypeParamDef,
    ParameterizedPersonality,
    PersonalityParameter,
    PersonalityStage,
)
from aquilon.aqdb.model.feature import host_features
from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates import (
    Plenary,
    PlenaryCollection,
    PlenaryParameterized,
    PlenaryResource,
    StructurePlenary,
)
from aquilon.worker.templates.entitlementutils import flatten_entitlements
from aquilon.worker.templates.panutils import (
    pan_append,
    pan_assign,
    pan_include,
    pan_include_if_exists,
    pan_variable,
    StructureTemplate,
)

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


class PlenaryParameterizedPersonality(PlenaryParameterized):
    prefix = "personality"

    @classmethod
    def template_name(cls, dbobj):
        return "{}/{}/{}/{}/config".format(
            cls.prefix,
            dbobj.name,
            dbobj.location.location_type,
            dbobj.location.name)

    def body(self, lines):
        flatten_entitlements(lines, self.dbobj, prefix='/')

        for resholder in self.dbobj.resholders:
            if resholder.location != self.dbobj.location:
                continue

            lines.append("")
            for resource in sorted(resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                res_path = PlenaryResource.template_name(resource)
                pan_append(
                    lines,
                    '/system/resources/{}'.format(resource.resource_type),
                    StructureTemplate(res_path))


Plenary.handlers[ParameterizedPersonality] = PlenaryParameterizedPersonality


class PlenaryPersonality(PlenaryCollection):

    def __init__(self, dbstage, logger=LOGGER, allow_incomplete=True):
        super(PlenaryPersonality, self).__init__(logger=logger,
                                                 allow_incomplete=allow_incomplete)

        self.append(PlenaryPersonalityBase.get_plenary(dbstage,
                                                       allow_incomplete=allow_incomplete))
        for defholder, dbparam in dbstage.parameters.items():
            if not isinstance(defholder, ArchetypeParamDef):
                continue
            self.append(PlenaryPersonalityParameter.get_plenary(dbparam,
                                                                allow_incomplete=allow_incomplete))

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

        eon_id_map = defaultdict(set)
        for grn_rec in self.dbobj.grns:
            eon_id_map[grn_rec.target].add(grn_rec.grn.eon_id)

        for target in sorted(eon_id_map):
            for eon_id in sorted(eon_id_map[target]):
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

        for dbfeature in sorted(frozenset()
                                .union(pre)
                                .union(post)
                                .intersection(self.dbobj.param_features),
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
