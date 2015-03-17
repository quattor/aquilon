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
from aquilon.aqdb.model import Personality, PersonalityParameter
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import set_parameter
from aquilon.worker.dbwrappers.personality import validate_personality_justification
from aquilon.worker.templates import Plenary


class CommandAddParameter(BrokerCommand):

    required_parameters = ['personality', 'path']

    def process_parameter(self, session, param_holder, feature, model,
                          interface, path, value, comments):
        return set_parameter(session, param_holder, feature, model, interface,
                             path, value, comments=comments, compel=False,
                             preclude=True)

    def render(self, session, logger, archetype, personality, feature, model,
               interface, path, user, value=None, comments=None,
               justification=None, reason=None, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if not dbpersonality.paramholder:
            dbpersonality.paramholder = PersonalityParameter()

        if not dbpersonality.archetype.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(dbpersonality.archetype))

        validate_personality_justification(dbpersonality, user, justification, reason)

        dbparameter = self.process_parameter(session, dbpersonality.paramholder,
                                             feature, model, interface, path,
                                             value, comments)
        session.add(dbparameter)
        session.flush()

        plenary = Plenary.get_plenary(dbpersonality, logger=logger)
        plenary.write()
