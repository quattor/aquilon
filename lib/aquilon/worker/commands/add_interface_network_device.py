# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
""" Contains the logic for `aq add interface --network_device`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 check_netdev_iftype)
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddInterfaceNetworkDevice(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["interface", "network_device", "iftype"]
    invalid_parameters = ["automac", "pg", "autopg", "model", "vendor",
                          "bus_address"]

    def render(self, session, logger, plenaries, interface, network_device,
               mac, iftype, comments, user, justification, reason, **arguments):
        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise ArgumentError("Cannot use argument --%s when adding an "
                                    "interface to a network device." % arg)

        check_netdev_iftype(iftype)

        dbnetdev = NetworkDevice.get_unique(session, network_device, compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbnetdev)
        cm.validate()

        oldinfo = DSDBRunner.snapshot_hw(dbnetdev)

        get_or_create_interface(session, dbnetdev, name=interface, mac=mac,
                                interface_type=iftype, comments=comments,
                                preclude=True)

        session.flush()

        plenaries.add(dbnetdev)
        plenaries.add(dbnetdev.host)

        with plenaries.transaction():
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbnetdev, oldinfo)
            dsdb_runner.commit_or_rollback("Could not update network device in DSDB")

        return
