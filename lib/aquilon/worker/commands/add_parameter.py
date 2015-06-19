# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Personality, Parameter, PersonalityParameter
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import (set_parameter,
                                                 get_feature_link)
from aquilon.worker.dbwrappers.personality import validate_personality_justification
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddParameter(BrokerCommand):

    required_parameters = ['personality', 'path']

    def process_parameter(self, session, dbstage, dblink, path, value):
        if not dbstage.paramholder:
            dbstage.paramholder = PersonalityParameter()
        if not dbstage.paramholder.parameter:
            dbstage.paramholder.parameter = Parameter(value={})

        set_parameter(session, dbstage.paramholder, dblink, path, value,
                      compel=False, preclude=True)

    def render(self, session, logger, archetype, personality, personality_stage,
               feature, model, interface, path, user, value=None,
               justification=None, reason=None, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if not dbpersonality.archetype.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(dbpersonality.archetype))

        dbstage = dbpersonality.active_stage(personality_stage)

        validate_personality_justification(dbstage, user, justification,
                                           reason)

        if feature:
            dblink = get_feature_link(session, feature, model, interface,
                                      dbstage)
        else:
            dblink = None

        self.process_parameter(session, dbstage, dblink, path, value)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbstage))
        plenaries.write()

        return
