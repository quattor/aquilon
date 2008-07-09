#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add tor_switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import create_machine
from aquilon.aqdb.switch_port import SwitchPort


class CommandAddTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch", "model", "rack"]

    @add_transaction
    @az_check
    def render(self, session, tor_switch, model, rack, serial,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            user, **arguments):
        dblocation = get_location(session, rack=rack)
        dbmodel = get_model(session, model)

        if dbmodel.machine_type not in ['tor_switch']:
            raise ArgumentError("The add_tor_switch command cannot add machines of type '%s'.  Try 'add machine'." %
                    dbmodel.machine_type)

        dbtor_switch = create_machine(session, tor_switch, dblocation, dbmodel,
            cpuname, cpuvendor, cpuspeed, cpucount, memory, serial)

        # FIXME: Hard-coded number of switch ports...
        switch_port_start = 1
        switch_port_count = 48
        switch_port_end = switch_port_start + switch_port_count
        for i in range(switch_port_start, switch_port_end):
            dbsp = SwitchPort(switch=dbtor_switch, port_number=i)
            session.save(dbsp)

        return


#if __name__=='__main__':
