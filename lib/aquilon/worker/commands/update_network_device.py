# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq update network_device`."""

from datetime import datetime

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.types import MACAddress
from aquilon.aqdb.model import Model, NetworkDevice, ObservedMac, Chassis, NetworkDeviceChassisSlot
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.hardware_entity import (update_primary_ip,
                                                       rename_hardware)
from aquilon.worker.dbwrappers.observed_mac import (
    update_or_create_observed_mac)
from aquilon.worker.dbwrappers.network_device import discover_network_device
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import PlenarySwitchData
from aquilon.utils import validate_json
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateNetworkDevice(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["network_device"]

    def render(self, session, logger, plenaries, network_device, model, type, ip, vendor,
               serial, rename_to, discovered_macs, clear, discover, comments, chassis, slot,
               clearchassis, multislot, user, justification, reason, exporter, **arguments):
        dbnetdev = NetworkDevice.get_unique(session, network_device, compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbnetdev)
        cm.validate()

        oldinfo = DSDBRunner.snapshot_hw(dbnetdev)
        plenaries.add(dbnetdev, cls=PlenarySwitchData)
        plenaries.add(dbnetdev)
        plenaries.add(dbnetdev.host)

        if discover:
            discover_network_device(session, logger, self.config,
                                    dbnetdev, False, exporter)

        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)
            if not dbmodel.model_type.isNetworkDeviceType():
                raise ArgumentError("This command can only be used to "
                                    "add network devices.")
            dbnetdev.model = dbmodel

        if clearchassis:
            del dbnetdev.chassis_slot[:]

        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            if slot is None:
                raise ArgumentError("The --chassis option requires a --slot.")
            dbnetdev.location = dbchassis.location
            self.adjust_slot(session, logger,
                             dbnetdev, dbchassis, slot, multislot)
        elif slot is not None:
            dbchassis = None
            for dbslot in dbnetdev.chassis_slot:
                if dbchassis and dbslot.chassis != dbchassis:
                    raise ArgumentError("Network Device in multiple chassis, please "
                                        "use --chassis argument.")
                dbchassis = dbslot.chassis
            if not dbchassis:
                raise ArgumentError("Option --slot requires --chassis "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbnetdev, dbchassis, slot, multislot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            loc_clear_chassis = False
            for dbslot in dbnetdev.chassis_slot:
                dbcl = dbslot.chassis.location
                if dbcl != dblocation:
                    if chassis or slot is not None:
                        raise ArgumentError("{0} conflicts with chassis {1!s} "
                                            "location {2}."
                                            .format(dblocation, dbslot.chassis,
                                                    dbcl))
                    else:
                        loc_clear_chassis = True
            if loc_clear_chassis:
                del dbnetdev.chassis_slot[:]
            dbnetdev.location = dblocation

        if serial is not None:
            dbnetdev.serial_no = serial

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        if type:
            NetworkDevice.check_type(type)
            dbnetdev.switch_type = type

        if ip:
            update_primary_ip(session, logger, dbnetdev, ip)

        if comments is not None:
            dbnetdev.comments = comments

        if rename_to:
            # Handling alias renaming would not be difficult in AQDB, but the
            # DSDB synchronization would be painful, so don't do that for now.
            # In theory we should check all configured IP addresses for aliases,
            # but this is the most common case
            if dbnetdev.primary_name and dbnetdev.primary_name.fqdn.aliases:
                raise ArgumentError("The network device has aliases and it cannot be "
                                    "renamed. Please remove all aliases first.")
            rename_hardware(session, dbnetdev, rename_to)

        if clear:
            session.query(ObservedMac).filter_by(network_device=dbnetdev).delete()

        if discovered_macs:
            validate_json(self.config, discovered_macs, "discovered_macs",
                          "discovered MACs")

            now = datetime.now()
            for (macaddr, port) in discovered_macs:
                update_or_create_observed_mac(session, dbnetdev, port,
                                              MACAddress(macaddr), now)

        session.flush()

        with plenaries.transaction():
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbnetdev, oldinfo)
            dsdb_runner.commit_or_rollback("Could not update network device in DSDB")

        return

    def adjust_slot(self, session, logger,
                    dbnetdev, dbchassis, slot, multislot):
        for dbslot in dbnetdev.chassis_slot:
            if dbslot.chassis == dbchassis and dbslot.slot_number == slot:
                return
            if dbslot.chassis != dbchassis and multislot:
                raise ArgumentError("Network Device cannot be in multiple chassis. "
                                    "Use --clearchassis to remove "
                                    "current chassis slot information.")
        if len(dbnetdev.chassis_slot) > 1 and not multislot:
            raise ArgumentError("Use --multislot to support a network device in more "
                                "than one slot, or --clearchassis to remove "
                                "current chassis slot information.")
        if not multislot:
            slots = ", ".join(str(dbslot.slot_number) for dbslot in
                              dbnetdev.chassis_slot)
            logger.info("Clearing {0:l} out of {1:l} slot(s) "
                        "{2}".format(dbnetdev, dbchassis, slots))
            del dbnetdev.chassis_slot[:]
        q = session.query(NetworkDeviceChassisSlot)
        q = q.filter_by(chassis=dbchassis, slot_number=slot)
        dbslot = q.first()
        if dbslot:
            if dbslot.network_device:
                raise ArgumentError("{0} slot {1} already has network device "
                                    "{2}.".format(dbchassis, slot,
                                                  dbslot.network_device.label))
        else:
            dbslot = NetworkDeviceChassisSlot(chassis=dbchassis, slot_number=slot)
        dbnetdev.chassis_slot.append(dbslot)
        return
