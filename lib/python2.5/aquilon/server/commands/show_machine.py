# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show machine`."""


from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.machine import get_machine
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
            # This command still mixes search/show facilities.
            # For now, warn if machine name not found (via get_machine), but
            # also allow the command to be used to check if the machine has
            # the requested attributes (via the standard query filters).
            # In the future, this should be clearly separated as 'show machine'
            # and 'search machine'.
            get_machine(session, machine)
            q = q.filter_by(name=machine)
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


