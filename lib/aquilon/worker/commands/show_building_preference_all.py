# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016 Contributor
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
""" Contains the logic for `aq show building preference --all`. """

from collections import defaultdict

from sqlalchemy.orm import aliased, contains_eager, joinedload, subqueryload
from sqlalchemy.sql import null

from aquilon.aqdb.model import BuildingPreference, Building, Archetype, Cluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.building_preference import ClusterBuildingPreference


class CommandShowBuildingPreferenceAll(BrokerCommand):

    def render(self, session, **_):
        AB = aliased(Building)
        BB = aliased(Building)

        q = session.query(BuildingPreference)
        q = q.join(AB, BuildingPreference.a)
        q = q.join(BB, BuildingPreference.b)
        q = q.join(Archetype)
        q = q.options(contains_eager('a', alias=AB),
                      contains_eager('b', alias=BB),
                      contains_eager('archetype'))

        pairs = defaultdict(list)

        for db_pref in q:
            key = db_pref.sorted_name + "," + db_pref.archetype.name
            pairs[key].append(db_pref)

        # Add clusters which have a preference override
        q = session.query(Cluster)
        q = q.filter(Cluster.preferred_location != null())
        q = q.options(subqueryload('_hosts'),
                      joinedload('_hosts.host'),
                      joinedload('_hosts.host.hardware_entity'),
                      joinedload('_hosts.host.hardware_entity.location'))
        for dbcluster in q:
            buildings = dbcluster.member_locations(location_class=Building)
            if len(buildings) != 2:
                continue

            key = ",".join(sorted(building.name for building in buildings))
            key = key + "," + dbcluster.archetype.name
            clpref = ClusterBuildingPreference(cluster=dbcluster)
            pairs[key].append(clpref)

        # Flatten lists within lists, need to return only a simple list
        return [item for key in sorted(pairs.keys()) for item in pairs[key]]
