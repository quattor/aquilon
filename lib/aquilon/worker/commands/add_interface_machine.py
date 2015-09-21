# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Contains the logic for `aq add interface --machine`."""

from aquilon.aqdb.model import Machine
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.machine import add_interface
from aquilon.worker.templates import Plenary, PlenaryCollection
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, automac, model,
               vendor, pg, autopg, iftype, type, bus_address, comments,
               **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)
        plenaries = PlenaryCollection(logger=logger)
        audit_results = []

        if type:
            self.deprecated_option("type", "Please use --iftype"
                                   "instead.", logger=logger, **arguments)
            if not iftype:
                iftype = type

        dbinterface = add_interface(self.config, session, logger, dbmachine,
                                    interface, vendor=vendor, model=model,
                                    iftype=iftype, mac=mac, automac=automac,
                                    pg=pg, autopg=autopg,
                                    bus_address=bus_address, comments=comments)

        if automac:
            audit_results.append(('mac', dbinterface.mac))
            logger.info("Selected MAC address {0!s} for {1:l}."
                        .format(dbinterface.mac, dbinterface))

        if autopg:
            if dbinterface.port_group:
                audit_results.append(('pg', dbinterface.port_group.name))
            else:
                audit_results.append(('pg', dbinterface.port_group_name))

        session.flush()

        plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.host:
            plenaries.append(Plenary.get_plenary(dbmachine.host))

        # Even though there may be removals going on the write key
        # should be sufficient here.
        dsdb_runner = DSDBRunner(logger=logger)
        with plenaries.transaction():
            dsdb_runner.update_host(dbmachine, oldinfo)
            dsdb_runner.commit_or_rollback("Could not update host in DSDB")

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return
