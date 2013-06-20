# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq add building`."""


from aquilon.aqdb.model import Building, City
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import add_location
from aquilon.worker.processes import DSDBRunner


class CommandAddBuilding(BrokerCommand):

    required_parameters = ["building", "city", "address"]

    def render(self, session, logger, building, city, fullname, comments,
               address, **arguments):
        dbcity = City.get_unique(session, city, compel=True)
        add_location(session, Building, building, dbcity, fullname=fullname,
                     address=address, comments=comments)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.add_building(building, city, address)
        if dbcity.campus:
            dsdb_runner.add_campus_building(dbcity.campus, building)
        dsdb_runner.commit_or_rollback()

        return
