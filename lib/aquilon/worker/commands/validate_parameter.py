# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
from aquilon.aqdb.model import Personality
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import validate_personality_config


class CommandValidateParameter(BrokerCommand):

    required_parameters = ["personality"]

    def render(self, session, logger, personality, personality_stage,
               archetype, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)

        errors = validate_personality_config(dbpersonality.active_stage(personality_stage))
        if errors:
            raise ArgumentError("Following required parameters have not been "
                                "specified:\n" +
                                "\n".join(error for error in errors))

        logger.client_info("All required parameters specified.")
        return
