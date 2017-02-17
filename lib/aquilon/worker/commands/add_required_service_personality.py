# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq add required service --personality`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (Personality, HostEnvironment, Service,
                                PersonalityServiceListItem)
from aquilon.worker.dbwrappers.change_management import validate_prod_personality


class CommandAddRequiredServicePersonality(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["service", "archetype", "personality"]

    def _update_dbobj(self, logger, dbstage, dbservice, dbenv):
        if dbservice in dbstage.required_services:
            raise ArgumentError("{0} is already required by {1:l}."
                                .format(dbservice, dbstage))

        if dbservice in dbstage.archetype.required_services and not dbenv:
            # This is not a hard error, because one may actually be in the
            # process of removing the requirement from the archetype level
            logger.client_info("Warning: {0} is already required by {1:l}. "
                               "Did you mean to use --environment_override?"
                               .format(dbservice, dbstage.archetype))

        psli = PersonalityServiceListItem(personality_stage=dbstage,
                                          service=dbservice,
                                          host_environment=dbenv)
        dbstage.required_services[dbservice] = psli

    def render(self, session, logger, plenaries, service, archetype, personality,
               personality_stage, environment_override, justification, reason,
               user, **_):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        dbpersonality.archetype.require_compileable("required services are not supported")

        dbstage = dbpersonality.active_stage(personality_stage)
        dbservice = Service.get_unique(session, service, compel=True)
        if environment_override:
            dbenv = HostEnvironment.get_instance(session, environment_override)
        else:
            dbenv = None
        validate_prod_personality(dbstage, user, justification, reason, logger)

        if dbstage.created_implicitly:
            plenaries.add(dbstage)

        self._update_dbobj(logger, dbstage, dbservice, dbenv)
        session.flush()

        plenaries.write()
        return
