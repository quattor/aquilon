#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show machine`."""


from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.hw.machine import Machine


class CommandShowMachine(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, machine, model, chassis, slot, **arguments):
        q = session.query(Machine)
        if machine:
            q = q.filter(Machine.name.like(machine + '%'))
        dblocation = get_location(session, **arguments)
        if dblocation:
            q = q.filter_by(location=dblocation)
        if chassis:
            dbchassis = get_system(session, chassis)
            q = q.join('chassis_slot')
            q = q.filter_by(chassis=dbchassis)
            q = q.reset_joinpoint()
        if slot:
            slot = force_int("slot", slot)
            q = q.join('chassis_slot')
            q = q.filter_by(slot_number=slot)
            q = q.reset_joinpoint()
        if model:
            dbmodel = get_model(session, model)
            q = q.filter_by(model=dbmodel)
        return q.all()


#if __name__=='__main__':
