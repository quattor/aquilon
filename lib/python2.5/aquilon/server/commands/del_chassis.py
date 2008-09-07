#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del chassis`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.aqdb.hw.chassis_slot import ChassisSlot


class CommandDelChassis(BrokerCommand):

    required_parameters = ["name"]

    @add_transaction
    @az_check
    def render(self, session, name, **arguments):
        dbchassis = get_system(session, name)
        if not isinstance(dbchassis, Chassis):
            raise ArgumentError("%s '%s' is not a chassis." %
                                (dbchassis.system_type, dbchassis.fqdn))
        q = session.query(ChassisSlot).filter_by(chassis=dbchassis)
        machine_count = q.count(ChassisSlot.machine_id != None)
        if machine_count:
            raise ArgumentError("Cannot remove chassis '%s': still in use by %d machines" %
                                (dbchassis.fqdn, machine_count))
        session.delete(dbchassis)
        return


#if __name__=='__main__':
