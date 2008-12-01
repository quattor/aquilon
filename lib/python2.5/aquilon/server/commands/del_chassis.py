# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del chassis`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.aqdb.hw.chassis_slot import ChassisSlot


class CommandDelChassis(BrokerCommand):

    required_parameters = ["chassis"]

    def render(self, session, chassis, **arguments):
        dbchassis = get_system(session, chassis, Chassis, 'Chassis')
        q = session.query(ChassisSlot).filter_by(chassis=dbchassis)
        machine_count = q.count(ChassisSlot.machine_id != None)
        if machine_count:
            raise ArgumentError("Cannot remove chassis '%s': still in use by %d machines" %
                                (dbchassis.fqdn, machine_count))

        for iface in dbchassis.interfaces:
            log.msg("Before deleting chassis '%s', removing interface '%s' [%s] boot=%s)" %
                    (dbchassis.fqdn, iface.name, iface.mac, iface.bootable))
            session.delete(iface)

        for iface in dbchassis.chassis_hw.interfaces:
            log.msg("Before deleting chassis '%s', removing hardware interface '%s' [%s] boot=%s)" %
                    (dbchassis.fqdn, iface.name, iface.mac, iface.bootable))
            session.delete(iface)

        session.delete(dbchassis.chassis_hw)
        session.delete(dbchassis)
        return


