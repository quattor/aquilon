# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017  Contributor
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

from collections import defaultdict

from sqlalchemy.orm import aliased, contains_eager, joinedload, subqueryload
from sqlalchemy.sql import or_, null

from aquilon.aqdb.model import (BuildingPreference, Building, Archetype, Cluster,
                                Personality, PersonalityStage)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList
from aquilon.worker.formats.building_preference import BuildingClusterPreference


class CommandSearchBuildingPreference(BrokerCommand):

    def render(self, session, building, building_pair, prefer, archetype,
               style, **_):
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

        bcprefs = defaultdict(list)

        for db_pref in q:
            key = db_pref.sorted_name + "," + db_pref.archetype.name
            bcprefs[key] = BuildingClusterPreference(db_pref.sorted_name,
                                                     db_pref.archetype,
                                                     [],
                                                     db_pref.prefer)

        # Search for cluster-specific building preference(s)
        cq = session.query(Cluster)
        cq = cq.filter(Cluster.preferred_location != null())
        cq = cq.options(subqueryload('_hosts'),
                        joinedload('_hosts.host'),
                        joinedload('_hosts.host.hardware_entity'),
                        joinedload('_hosts.host.hardware_entity.location'))

        if prefer:
            cq = cq.filter_by(preferred_location=db_building)
        if archetype:
            cq = cq.join(PersonalityStage, Personality)
            cq = cq.filter_by(archetype=dbarchetype)

        for dbcluster in cq.all():
            buildings = dbcluster.member_locations(location_class=Building)
            if building:
                # Check if this cluster involves the specified building
                # (dbbuilding)
                if dbbuilding not in buildings:
                    continue
            if building_pair:
                # Check if this cluster involves _at least_ the specified
                # buildings (pair.{a,b})
                if (pair.a not in buildings) or (pair.b not in buildings):
                    continue

            sortname = ",".join(sorted(building.name for building in buildings))
            key = sortname + "," + dbcluster.personality.archetype.name

            if key in bcprefs:
                bcprefs[key].clusters.append(dbcluster)
            else:
                bcprefs[key] = BuildingClusterPreference(sortname,
                                                         dbcluster.personality.archetype,
                                                         [dbcluster])

        return [bcprefs[key] for key in sorted(bcprefs.keys())]
