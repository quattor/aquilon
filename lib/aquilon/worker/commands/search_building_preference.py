# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
""" Contains the logic for `aq search building preference`. """

from sqlalchemy.orm import aliased, contains_eager
from sqlalchemy.sql import or_

from aquilon.aqdb.model import BuildingPreference, Building, Archetype
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList


class CommandSearchBuildingPreference(BrokerCommand):

    def render(self, session, building, building_pair, prefer, archetype,
               fullinfo, style, **_):
        AB = aliased(Building)
        BB = aliased(Building)

        q = session.query(BuildingPreference)

        if prefer:
            db_building = Building.get_unique(session, prefer, compel=True)
            q = q.filter_by(prefer=db_building)

        if building_pair:
            pair = BuildingPreference.parse_pair(session, building_pair)
            q = q.filter_by(a=pair.a, b=pair.b)

        if building:
            dbbuilding = Building.get_unique(session, building, compel=True)
            q = q.filter(or_(BuildingPreference.a == dbbuilding,
                             BuildingPreference.b == dbbuilding))

        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            q = q.filter_by(archetype=dbarchetype)

        q = q.join(AB, BuildingPreference.a)
        q = q.join(BB, BuildingPreference.b)
        q = q.join(Archetype)
        q = q.options(contains_eager('a', alias=AB),
                      contains_eager('b', alias=BB),
                      contains_eager('archetype'))
        q = q.order_by(AB.name, BB.name, Archetype.name)

        if fullinfo or style != "raw":
            return q.all()
        return StringAttributeList(q.all(), "qualified_name")
