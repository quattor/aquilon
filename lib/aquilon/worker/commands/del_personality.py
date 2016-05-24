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
"""Contains the logic for `aq del personality`."""

from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Personality, PersonalityStage, CompileableMixin,
                                Cluster)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandDelPersonality(BrokerCommand):

    required_parameters = ["personality", "archetype"]

    def render(self, session, logger, personality, archetype, **_):
        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

        for cls_ in CompileableMixin.__subclasses__():
            q = session.query(*inspect(cls_).mapper.primary_key)
            q = q.join(PersonalityStage)
            q = q.filter_by(personality=dbpersona)
            if q.count():
                raise ArgumentError("{0} is still in use and cannot be deleted."
                                    .format(dbpersona))

        plenaries = PlenaryCollection(logger=logger)
        plenaries.extend(map(Plenary.get_plenary, dbpersona.stages.values()))

        q = session.query(Cluster)
        q = q.filter(Cluster.allowed_personalities.contains(dbpersona))
        for dbobj in q:
            plenaries.append(Plenary.get_plenary(dbobj))

        session.delete(dbpersona)

        session.flush()

        plenaries.write()

        return
