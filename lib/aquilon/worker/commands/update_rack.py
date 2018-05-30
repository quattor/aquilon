# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Contains the logic for `aq update rack`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Rack, Machine
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location, update_location
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.processes import DSDBRunner


class CommandUpdateRack(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["rack"]

    def render(self, session, plenaries, rack, row, column, room, building, bunker, uri,
               fullname, default_dns_domain, comments, user, justification, reason, logger, **arguments):
        dbrack = Rack.get_unique(session, rack, compel=True)

        dsdb_runner = DSDBRunner(logger=logger)
        snapshot_rack = dsdb_runner.snapshot(dbrack)
        q = session.query(Machine)
        q = q.filter(Machine.location_id.in_(dbrack.offspring_ids()))

        if row or column or bunker or room or building:
            # Validate ChangeManagement
            cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
            cm.consider(q)
            cm.validate()

        if row is not None:
            dbrack.rack_row = row
        if column is not None:
            dbrack.rack_column = column

        update_location(dbrack, fullname=fullname, comments=comments, uri=uri,
                        default_dns_domain=default_dns_domain)

        if bunker or room or building:
            dbparent = get_location(session, bunker=bunker, room=room,
                                    building=building)
            # This one would change the template's locations hence forbidden
            if dbparent.building != dbrack.building:
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change buildings.  {0} is in {1} "
                                    "while {2} is in {3}.".format(
                                        dbparent, dbparent.building,
                                        dbrack, dbrack.building))
            dbrack.update_parent(parent=dbparent)

        session.flush()

        dsdb_runner.update_rack(dbrack, snapshot_rack)
        dsdb_runner.commit_or_rollback()

        plenaries.add(q)
        plenaries.write()
