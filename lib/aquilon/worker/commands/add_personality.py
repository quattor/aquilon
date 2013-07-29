# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
from ConfigParser import NoSectionError, NoOptionError

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Archetype, Personality,
                                Parameter, HostEnvironment,
                                PersonalityServiceMap,
                                PersonalityParameter)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.parameter import get_parameters
from aquilon.worker.dbwrappers.feature import add_link
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.templates.personality import PlenaryPersonality

VALID_PERSONALITY_RE = re.compile('^[a-zA-Z0-9_-]+\/?[a-zA-Z0-9_-]+$')


class CommandAddPersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, archetype,
               grn, eon_id, host_environment, comments,
               cluster_required, copy_from, config_override, **arguments):
        if not VALID_PERSONALITY_RE.match(personality):
            raise ArgumentError("Personality name '%s' is not valid." %
                                personality)
        if not (grn or eon_id):
            raise ArgumentError("GRN or EON ID is required for adding a "
                                "personality.")

        dbarchetype = Archetype.get_unique(session, archetype, compel=True)

        if not host_environment:
            try:
                host_environment = self.config.get("archetype_" + archetype,
                                                   "default_environment")
            except (NoSectionError, NoOptionError):
                raise ArgumentError("Default environment is not configured "
                                    "for {0:l}, please specify "
                                    "--host_environment.".format(dbarchetype))

        HostEnvironment.polymorphic_subclass(host_environment,
                                             "Unknown environment name")
        Personality.validate_env_in_name(personality, host_environment)
        host_env = HostEnvironment.get_unique(session, host_environment, compel=True)

        Personality.get_unique(session, archetype=dbarchetype, name=personality,
                               preclude=True)

        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)

        dbpersona = Personality(name=personality, archetype=dbarchetype,
                                cluster_required=bool(cluster_required),
                                host_environment=host_env, owner_grn=dbgrn,
                                comments=comments,
                                config_override=config_override)
        session.add(dbpersona)

        if self.config.has_option("archetype_" + archetype, "default_grn_target"):
            dbpersona.grns.append((dbpersona, dbgrn,
                                   self.config.get("archetype_" + archetype,
                                                   "default_grn_target")))

        if copy_from:
            ## copy config data
            dbfrom_persona = Personality.get_unique(session,
                                                    archetype=dbarchetype,
                                                    name=copy_from,
                                                    compel=True)

            src_parameters = get_parameters(session,
                                            personality=dbfrom_persona)
            db_param_holder = PersonalityParameter(personality=dbpersona)

            for param in src_parameters:
                dbparameter = Parameter(value=param.value,
                                        comments=param.comments,
                                        holder=db_param_holder)
                session.add(dbparameter)

            for link in dbfrom_persona.features:
                params = {}
                params["personality"] = dbpersona
                if link.model:
                    params["model"] = link.model
                if link.interface_name:
                    params["interface_name"] = link.interface_name

                add_link(session, logger, link.feature, params)

            ## service maps
            q = session.query(PersonalityServiceMap).filter_by(personality=dbfrom_persona)

            for sm in q.all():
                dbmap = PersonalityServiceMap(service_instance=sm.service_instance,
                                              location=sm.location,
                                              network=sm.network,
                                              personality=dbpersona)
                session.add(dbmap)

            ## required services
            dbpersona.services.extend(dbfrom_persona.services)

        session.flush()

        plenary = PlenaryPersonality(dbpersona, logger=logger)
        plenary.write()
        return
