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
""" Contains the logic for `aq update building preference`. """

from aquilon.aqdb.model import BuildingPreference, Building
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_archetype
from aquilon.worker.dbwrappers.cluster import get_clusters_by_locations


class CommandUpdateBuildingPreference(BrokerCommand):

    requires_plenaries = True
    required_parameters = ["building_pair", "archetype"]

    def render(self, session, logger, plenaries, building_pair, archetype,
               prefer, justification, reason, user, **_):
        db_pref = BuildingPreference.get_unique(session,
                                                building_pair=building_pair,
                                                archetype=archetype,
                                                compel=True)
        db_pref.lock_row()

        validate_prod_archetype(db_pref.archetype, user, justification, reason, logger)

        for db_clus in get_clusters_by_locations(session, (db_pref.a, db_pref.b),
                                                 db_pref.archetype):
            plenaries.add(db_clus)

        if prefer:
            dbbuilding = Building.get_unique(session, prefer, compel=True)
            db_pref.prefer = dbbuilding

        session.flush()

        # FIXME: for large numbers of affected clusters, this may take a little
        # while -- refactor some feedback into the plenaries.write() where
        # verbose=True.

        plenaries.write(verbose=True)

        return
