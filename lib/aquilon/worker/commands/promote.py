# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Contains the logic for `aq promote`."""

from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Personality, PersonalityStage, Host, Cluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandPromote(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, archetype, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if "next" not in dbpersonality.stages:
            raise ArgumentError("There is no next stage to promote.")

        if "previous" in dbpersonality.stages:
            dbstage = dbpersonality.stages["previous"]
            q1 = session.query(Host.hardware_entity_id)
            q1 = q1.filter_by(personality_stage=dbstage)

            q2 = session.query(Cluster.id)
            q2 = q2.filter_by(personality_stage=dbstage)

            if q1.count() or q2.count():
                raise ArgumentError("The previous stage of the personality "
                                    "is still in use, promotion is not "
                                    "possible.")

            del dbpersonality.stages["previous"]

        plenaries = PlenaryCollection(logger=logger)

        current = dbpersonality.stages["current"]
        next = dbpersonality.stages["next"]

        plenaries.append(Plenary.get_plenary(current))
        plenaries.append(Plenary.get_plenary(next))

        with session.no_autoflush:
            for cls in (Host, Cluster):
                q = session.query(cls)
                q = q.join(PersonalityStage)
                q = q.filter_by(personality=dbpersonality)
                q = q.options(contains_eager('personality_stage'))

                # We need to refresh all plenaries, even if the stage does not
                # change
                for dbobj in q:
                    plenaries.append(Plenary.get_plenary(dbobj))
                    dbobj.personality_stage = next

            current.name = "previous"
            next.name = "current"
            session.expire(dbpersonality, ['stages'])

        session.flush()

        plenaries.write()

        return
