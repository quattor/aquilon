# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2018  Contributor
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
""" Contains the logic for `aq add interface` for simple devices. """

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import NetworkDevice
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.hardware_entity import get_hardware
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 check_netdev_iftype)
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddInterface(BrokerCommand):

    requires_plenaries = True
    required_parameters = ["interface"]
    invalid_parameters = ["automac", "pg", "autopg", "bus_address"]

    def get_plenaries(self, dbhw_ent, plenaries):
        pass

    def render(self, session, logger, plenaries, interface, mac, iftype, model,
               vendor, comments, user, justification, reason, **arguments):
        dbhw_ent = get_hardware(session, **arguments)

        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise UnimplementedError("Argument --%s is not allowed for %s." %
                                         (arg, dbhw_ent._get_class_label(True)))

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbhw_ent)
        cm.validate()

        # FIXME: move this logic to the model
        if isinstance(dbhw_ent, NetworkDevice):
            check_netdev_iftype(iftype)
        else:
            if not iftype:
                iftype = "oa"
            if iftype != "oa":
                raise ArgumentError("Only 'oa' is allowed as the interface type.")

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        get_or_create_interface(session, dbhw_ent, name=interface, mac=mac,
                                interface_type=iftype, model=model,
                                vendor=vendor, comments=comments, preclude=True)

        session.flush()

        self.get_plenaries(dbhw_ent, plenaries)

        with plenaries.transaction():
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbhw_ent, oldinfo)
            dsdb_runner.commit_or_rollback("Could not update entry in DSDB")

        return
