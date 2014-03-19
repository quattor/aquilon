# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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

from aquilon.aqdb.types import NetworkDeviceType
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Model, NetworkDevice, ObservedMac
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.hardware_entity import (update_primary_ip,
                                                       rename_hardware)
from aquilon.worker.dbwrappers.observed_mac import (
    update_or_create_observed_mac)
from aquilon.worker.dbwrappers.network_device import discover_network_device
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.switchdata import PlenarySwitchData


class CommandUpdateNetworkDevice(BrokerCommand):

    required_parameters = ["network_device"]

    def render(self, session, logger, network_device, model, type, ip, vendor,
               serial, rename_to, discovered_macs, clear, discover, comments,
               **arguments):
        dbnetdev = NetworkDevice.get_unique(session, network_device, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbnetdev)
        plenary = PlenarySwitchData.get_plenary(dbnetdev, logger=logger)

        if discover:
            discover_network_device(session, logger, self.config,
                                    dbnetdev, False)

        if vendor and not model:
            model = dbnetdev.model.name
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)
            if not dbmodel.model_type.isNetworkDeviceType():
                raise ArgumentError("This command can only be used to "
                                    "add network devices.")
            dbnetdev.model = dbmodel

        dblocation = get_location(session, **arguments)
        if dblocation:
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
            now = datetime.now()
            for (macaddr, port) in discovered_macs:
                update_or_create_observed_mac(session, dbnetdev, port,
                                              macaddr, now)

        session.flush()

        with plenary.get_key():
            plenary.stash()
            try:
                plenary.write(locked=True)

                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbnetdev, oldinfo)
                dsdb_runner.commit_or_rollback("Could not update network device in DSDB")
            except:
                plenary.restore_stash()
                raise

        return
