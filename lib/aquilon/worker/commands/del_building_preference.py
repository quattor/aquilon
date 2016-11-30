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
""" Contains the logic for `aq del building preference`. """

from aquilon.aqdb.model import BuildingPreference
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_archetype
from aquilon.worker.dbwrappers.cluster import get_clusters_by_locations
from aquilon.worker.templates import PlenaryCollection, Plenary


class CommandDelBuildingPreference(BrokerCommand):

    required_parameters = ["building_pair", "archetype"]

    def render(self, session, logger, building_pair, archetype, justification,
               reason, user, **_):
        db_pref = BuildingPreference.get_unique(session,
                                                building_pair=building_pair,
                                                archetype=archetype,
                                                compel=True)

        validate_prod_archetype(db_pref.archetype, user, justification, reason)

        plenaries = PlenaryCollection(logger=logger)
        for db_clus in get_clusters_by_locations(session, (db_pref.a, db_pref.b),
                                                 db_pref.archetype):
            plenaries.append(Plenary.get_plenary(db_clus))

        session.delete(db_pref)
        session.flush()

        plenaries.write(verbose=True)

        return
