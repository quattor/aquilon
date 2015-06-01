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
"""Contains the logic for `aq add personality`."""

import re
from six.moves.configparser import NoSectionError, NoOptionError  # pylint: disable=F0401

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Archetype, Personality, PersonalityStage,
                                PersonalityGrnMap, HostEnvironment,
                                PersonalityServiceMap)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.templates import Plenary, PlenaryCollection

VALID_PERSONALITY_RE = re.compile(r'^[a-zA-Z0-9_-]+\/?[a-zA-Z0-9_-]+$')


class CommandAddPersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, archetype, grn, eon_id,
               host_environment, comments, cluster_required, copy_from,
               copy_stage, config_override, staged, **arguments):
        if not VALID_PERSONALITY_RE.match(personality):
            raise ArgumentError("Personality name '%s' is not valid." %
                                personality)

        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        section = "archetype_" + dbarchetype.name

        # If we're cloning a personality, read defaults from the cloned
        # object
        if copy_from:
            dbfrom_persona = Personality.get_unique(session,
                                                    archetype=dbarchetype,
                                                    name=copy_from, compel=True)
            if not grn and not eon_id:
                eon_id = dbfrom_persona.owner_grn.eon_id
            if not host_environment:
                host_environment = dbfrom_persona.host_environment.name
            if not cluster_required:
                cluster_required = dbfrom_persona.cluster_required
            if comments is None:
                comments = dbfrom_persona.comments
            if staged is None:
                staged = dbfrom_persona.staged

            if dbfrom_persona.config_override:
                logger.warning("{0} has config_override set. This setting will "
                               "not be copied, you will need to set it separately "
                               "on the new personality if needed."
                               .format(dbfrom_persona))
            dbfrom_vers = dbfrom_persona.default_stage(copy_stage)

        if not grn and not eon_id:
            raise ArgumentError("GRN or EON ID is required for adding a "
                                "personality.")

        if not host_environment:
            try:
                host_environment = self.config.get(section,
                                                   "default_environment")
            except (NoSectionError, NoOptionError):
                raise ArgumentError("Default environment is not configured "
                                    "for {0:l}, please specify "
                                    "--host_environment.".format(dbarchetype))

        # Placing this check here means legacy personalities cannot be cloned,
        # which is fine.
        if host_environment == 'legacy':
            raise ArgumentError("Legacy is not a valid environment for a new personality.")

        dbhost_env = HostEnvironment.get_instance(session, host_environment)
        Personality.validate_env_in_name(personality, dbhost_env.name)

        Personality.get_unique(session, archetype=dbarchetype, name=personality,
                               preclude=True)

        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)

        dbpersona = Personality(name=personality, archetype=dbarchetype,
                                cluster_required=cluster_required,
                                host_environment=dbhost_env, owner_grn=dbgrn,
                                staged=staged, comments=comments,
                                config_override=config_override)
        session.add(dbpersona)

        if staged:
            initial_stage = "next"
        else:
            initial_stage = "current"

        if copy_from:
            dbstage = dbfrom_vers.copy(name=initial_stage)
            dbpersona.stages[initial_stage] = dbstage

            q = session.query(PersonalityServiceMap)
            q = q.filter_by(personality=dbfrom_persona)
            for src_map in q:
                dst_map = PersonalityServiceMap(service_instance=src_map.service_instance,
                                                location=src_map.location,
                                                network=src_map.network,
                                                personality=dbpersona)
                session.add(dst_map)

            # TODO: should we copy root users and netgroups? Not doing so is
            # safer.
        else:
            dbstage = PersonalityStage(name=initial_stage)
            dbpersona.stages[initial_stage] = dbstage

            if self.config.has_option(section, "default_grn_target"):
                target = self.config.get(section, "default_grn_target")
                dbstage.grns.append(PersonalityGrnMap(grn=dbgrn, target=target))

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbstage))
        plenaries.write()

        return
