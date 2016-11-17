# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq del personality --personality_stage`."""

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import Personality, Host, Cluster
from aquilon.worker.broker import BrokerCommand


class CommandDelPersonalityPersonalityStage(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["personality", "archetype", "personality_stage"]

    def render(self, session, logger, plenaries, personality, archetype,
               personality_stage, **_):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        dbstage = dbpersonality.active_stage(personality_stage)

        if dbstage.name != "next":
            raise UnimplementedError("Only the 'next' stage can be deleted.")

        if dbpersonality.is_cluster:
            q = session.query(Cluster.id)
        else:
            q = session.query(Host.hardware_entity_id)
        q = q.filter_by(personality_stage=dbstage)
        if q.count():
            raise ArgumentError("{0} is still in use and cannot be deleted."
                                .format(dbstage))

        plenaries.add(dbstage)

        del dbpersonality.stages[personality_stage]

        session.flush()

        plenaries.write()

        return
