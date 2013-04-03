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
"""Contains the logic for `aq add campus`."""

from aquilon.aqdb.model import Country, Campus
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import add_location
from aquilon.worker.processes import DSDBRunner


class CommandAddCampus(BrokerCommand):

    required_parameters = ["country", "campus"]

    def render(self, session, logger, campus, country, fullname, comments,
               **arguments):
        dbcountry = Country.get_unique(session, country, compel=True)
        add_location(session, Campus, campus, dbcountry, fullname=fullname,
                     comments=comments)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.add_campus(campus, comments)
        dsdb_runner.commit_or_rollback()

        return
