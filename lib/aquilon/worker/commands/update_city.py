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
"""Contains the logic for `aq update city`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Machine
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.location import get_location, update_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUpdateCity(BrokerCommand):

    required_parameters = ["city"]

    def render(self, session, logger, city, timezone, fullname, campus,
               default_dns_domain, comments, **arguments):
        dbcity = get_location(session, city=city)

        # Updating machine templates is expensive, so only do that if needed
        update_machines = False

        if timezone is not None:
            dbcity.timezone = timezone

        update_location(dbcity, default_dns_domain=default_dns_domain,
                        fullname=fullname, comments=comments)

        prev_campus = None
        dsdb_runner = None
        dsdb_runner = DSDBRunner(logger=logger)
        if campus is not None:
            dbcampus = get_location(session, campus=campus)
            # This one would change the template's locations hence forbidden
            if dbcampus.hub != dbcity.hub:
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change campus.  {0} is in {1:l}, "
                                    "while {2:l} is in {3:l}.".format(
                                        dbcampus, dbcampus.hub,
                                        dbcity, dbcity.hub))

            if dbcity.campus:
                prev_campus = dbcity.campus
            dbcity.update_parent(parent=dbcampus)
            update_machines = True

        session.flush()

        if campus is not None:
            if prev_campus:
                prev_name = prev_campus.name
            else:
                prev_name = None
            dsdb_runner.update_city(city, dbcampus.name, prev_name)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbcity))

        if update_machines:
            q = session.query(Machine)
            q = q.filter(Machine.location_id.in_(dbcity.offspring_ids()))
            logger.client_info("Updating %d machines..." % q.count())
            for dbmachine in q:
                plenaries.append(Plenary.get_plenary(dbmachine))

        count = plenaries.write()
        dsdb_runner.commit_or_rollback()
        logger.client_info("Flushed %d templates." % count)
