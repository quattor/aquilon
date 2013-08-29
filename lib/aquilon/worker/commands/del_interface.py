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
"""Contains the logic for `aq del interface`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Chassis, Machine, Switch, Interface
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.interface import assign_address
from aquilon.worker.templates import Plenary


class _Goto(Exception):
    pass


class CommandDelInterface(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, interface, machine, switch, chassis, mac,
               user, **arguments):

        if not (machine or switch or chassis or mac):
            raise ArgumentError("Please specify at least one of --chassis, "
                                "--machine, --switch or --mac.")

        if machine:
            dbhw_ent = Machine.get_unique(session, machine, compel=True)
        elif switch:
            dbhw_ent = Switch.get_unique(session, switch, compel=True)
        elif chassis:
            dbhw_ent = Chassis.get_unique(session, chassis, compel=True)
        else:
            dbhw_ent = None

        dbinterface = Interface.get_unique(session, hardware_entity=dbhw_ent,
                                           name=interface, mac=mac, compel=True)
        if not dbhw_ent:
            dbhw_ent = dbinterface.hardware_entity

        if dbinterface.vlans:
            vlans = ", ".join([iface.name for iface in
                               dbinterface.vlans.values()])
            raise ArgumentError("{0} is the parent of the following VLAN "
                                "interfaces, delete them first: "
                                "{1}.".format(dbinterface, vlans))

        if dbinterface.slaves:
            slaves = ", ".join([iface.name for iface in dbinterface.slaves])
            raise ArgumentError("{0} is the master of the following slave "
                                "interfaces, delete them first: "
                                "{1}.".format(dbinterface, slaves))

        try:
            for addr in dbinterface.assignments:
                if addr.ip != dbhw_ent.primary_ip:
                    continue

                # Special handling: if this interface was created automatically,
                # and there is exactly one other interface with no IP address,
                # then re-assign the primary address to that interface
                if not dbinterface.mac and dbinterface.comments is not None and \
                   dbinterface.comments.startswith("Created automatically") and \
                   len(dbhw_ent.interfaces) == 2:
                    if dbinterface == dbhw_ent.interfaces[0]:
                        other = dbhw_ent.interfaces[1]
                    else:
                        other = dbhw_ent.interfaces[0]

                    if len(other.assignments) == 0:
                        assign_address(other, dbhw_ent.primary_ip,
                                       dbhw_ent.primary_name.network,
                                       logger=logger)
                        dbinterface.addresses.remove(dbhw_ent.primary_ip)
                        raise _Goto

                # If this is a machine, it is possible to delete the host to get rid
                # of the primary name
                if dbhw_ent.hardware_type == "machine":
                    msg = "  You should delete the host first."
                else:
                    msg = ""

                raise ArgumentError("{0} holds the primary address of the {1:cl}, "
                                    "therefore it cannot be deleted."
                                    "{2}".format(dbinterface, dbhw_ent, msg))
        except _Goto:
            pass

        addrs = ", ".join(["%s: %s" % (addr.logical_name, addr.ip) for addr in
                           dbinterface.assignments])
        if addrs:
            raise ArgumentError("{0} still has the following addresses "
                                "configured, delete them first: "
                                "{1}.".format(dbinterface, addrs))

        dbhw_ent.interfaces.remove(dbinterface)
        session.flush()

        if dbhw_ent.hardware_type == 'machine':
            plenary_info = Plenary.get_plenary(dbhw_ent, logger=logger)
            plenary_info.write()
        return
