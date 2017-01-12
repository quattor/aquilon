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
""" Contains the logic for `aq add building preference`. """

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import BuildingPreference, Building, Archetype
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_archetype
from aquilon.worker.dbwrappers.cluster import get_clusters_by_locations
from aquilon.worker.templates import PlenaryCollection, Plenary


class CommandAddBuildingPreference(BrokerCommand):

    required_parameters = ["building_pair", "prefer", "archetype"]

    def render(self, session, logger, building_pair, prefer, archetype,
               justification, reason, user, **_):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        validate_prod_archetype(dbarchetype, user, justification, reason, logger)
        if not dbarchetype.cluster_type:
            raise ArgumentError("{0} is not a cluster archetype."
                                .format(dbarchetype))

        pair = BuildingPreference.parse_pair(session, building_pair)
        dbbuilding = Building.get_unique(session, prefer, compel=True)

        BuildingPreference.get_unique(session, building_pair=pair,
                                      archetype=dbarchetype, preclude=True)

        db_pref = BuildingPreference(a=pair.a, b=pair.b,
                                     archetype=dbarchetype, prefer=dbbuilding)
        session.add(db_pref)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        for db_clus in get_clusters_by_locations(session, pair, dbarchetype):
            plenaries.append(Plenary.get_plenary(db_clus))

        plenaries.write(verbose=True)

        return
