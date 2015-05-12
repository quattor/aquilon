# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013,2014,2015  Contributor
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
from aquilon.aqdb.model import Personality, Service
from aquilon.worker.dbwrappers.personality import validate_personality_justification


class CommandAddRequiredServicePersonality(BrokerCommand):

    required_parameters = ["service", "archetype", "personality"]

    def _update_dbobj(self, dbstage, dbservice):
        if dbservice in dbstage.services:
            raise ArgumentError("{0} is already required by {1:l}."
                                .format(dbservice, dbstage))
        dbstage.services.append(dbservice)

    def render(self, session, service, archetype, personality,
               personality_stage, justification, reason, user, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        dbstage = dbpersonality.active_stage(personality_stage)
        validate_personality_justification(dbstage, user, justification,
                                           reason)
        dbservice = Service.get_unique(session, service, compel=True)

        self._update_dbobj(dbstage, dbservice)
        session.flush()
        return
