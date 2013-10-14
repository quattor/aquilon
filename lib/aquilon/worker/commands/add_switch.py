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
"""Contains the logic for `aq add switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.types import NetworkDeviceType
from aquilon.aqdb.model import NetworkDevice, Model
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 assign_address)
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import Plenary


class CommandAddSwitch(BrokerCommand):

    required_parameters = ["switch", "model", "rack", "type", "ip"]

    def render(self, session, logger, switch, label, model, rack, type, ip,
               interface, mac, vendor, serial, comments, **arguments):
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   compel=True)

        if not dbmodel.model_type.isNetworkDeviceType():
            raise ArgumentError("This command can only be used to "
                                "add network devices.")

        dblocation = get_location(session, rack=rack)

        dbdns_rec, newly_created = grab_address(session, switch, ip,
                                                allow_restricted_domain=True,
                                                allow_reserved=True,
                                                preclude=True)
        if not label:
            label = dbdns_rec.fqdn.name
            try:
                NetworkDevice.check_label(label)
            except ArgumentError:
                raise ArgumentError("Could not deduce a valid hardware label "
                                    "from the switch name.  Please specify "
                                    "--label.")

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        dbnetdev = NetworkDevice(label=label, switch_type=type, 
                                 location=dblocation, model=dbmodel, 
                                 serial_no=serial, comments=comments)
        session.add(dbnetdev)
        dbnetdev.primary_name = dbdns_rec

        # FIXME: get default name from the model
        iftype = "oa"
        if not interface:
            interface = "xge"
            ifcomments = "Created automatically by add_switch"
        else:
            ifcomments = None
            if interface.lower().startswith("lo"):
                iftype = "loopback"

        dbinterface = get_or_create_interface(session, dbnetdev,
                                              name=interface, mac=mac,
                                              interface_type=iftype,
                                              comments=ifcomments)
        dbnetwork = get_net_id_from_ip(session, ip)
        # TODO: should we call check_ip_restrictions() here?
        assign_address(dbinterface, ip, dbnetwork, logger=logger)

        session.flush()

        plenary = Plenary.get_plenary(dbnetdev, logger=logger)
        with plenary.get_key():
            plenary.stash()
            try:
                plenary.write(locked=True)
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbnetdev, None)
                dsdb_runner.commit_or_rollback("Could not add switch to DSDB")
            except:
                plenary.restore_stash()
                raise

        return
