# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2017  Contributor
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
""" Contains the logic for `aq show building preference --cluster`. """

from collections import defaultdict

from sqlalchemy.orm import aliased, contains_eager, joinedload, subqueryload
from sqlalchemy.sql import and_, null

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (BuildingPreference, Building, Archetype, Cluster,
                                Personality, PersonalityStage)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.building_preference import BuildingClusterPreference


class CommandShowBuildingPreferenceCluster(BrokerCommand):

    def render(self, session, logger, cluster, **_):
        AB = aliased(Building)
        BB = aliased(Building)

        q = session.query(Cluster)
        q = q.filter(Cluster.cluster_type != 'meta')
        q = q.filter_by(name=cluster)
        q = q.join(PersonalityStage, Personality, Archetype)
        q = q.options(subqueryload('_hosts'),
                      joinedload('_hosts.host'),
                      joinedload('_hosts.host.hardware_entity'),
                      joinedload('_hosts.host.hardware_entity.location'))

        dbcluster = q.first()

        if dbcluster is None:
            raise NotFoundException("Cluster %s not found." % cluster)

        #if dbcluster.preferred_location is not None:
        #    return ClusterBuildingPreference(cluster=dbcluster)

        # See if there's a preference for building(s)
        buildings = dbcluster.member_locations(location_class=Building)
        sortname = ",".join(sorted(building.name for building in buildings))

        if len(buildings) == 2:
            AB = aliased(Building)
            BB = aliased(Building)

            q = session.query(BuildingPreference)
            q = q.join(AB, BuildingPreference.a)
            q = q.join(BB, BuildingPreference.b)
            q = q.join(Archetype)
            q = q.options(contains_eager('a', alias=AB),
                          contains_eager('b', alias=BB),
                          contains_eager('archetype'))

            bldgs = BuildingPreference.ordered_pair(buildings)
            q = q.filter(and_(BuildingPreference.a == bldgs[0],
                              BuildingPreference.b == bldgs[1],
                              BuildingPreference.archetype == dbcluster.personality.archetype))

            bpref = q.first()
            if bpref is not None:
                # Have a building pair that affects this cluster
                return BuildingClusterPreference(bpref.sorted_name,
                                                 dbcluster.personality.archetype,
                                                 [dbcluster],
                                                 bpref.prefer)
            else:
                return BuildingClusterPreference(sortname,
                                                 dbcluster.personality.archetype,
                                                 [dbcluster])

        if dbcluster.preferred_location is not None:
            # Not good -- cluster preferred location with <>2 buildings involved
            logger.client_info("Warning: cluster {0.name} has preferred location "
                               "({1.name}), but not in 2 buildings (in {2})"
                               .format(dbcluster, dbcluster.preferred_location,
                                       len(buildings)))
            return BuildingClusterPreference(sortname,
                                             dbcluster.personality.archetype,
                                             [dbcluster])

        raise NotFoundException("Cluster {0.name} has no building preference."
                                .format(dbcluster))

