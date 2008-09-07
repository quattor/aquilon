#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add machine`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import create_machine, get_machine
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.aqdb.hw.chassis_slot import ChassisSlot


class CommandAddMachine(BrokerCommand):

    required_parameters = ["machine", "model"]

    @add_transaction
    @az_check
    # arguments will contain one of --chassis --rack or --desk
    def render(self, session, machine, model, serial, chassis, slot,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            user, **arguments):
        dblocation = get_location(session, **arguments)
        if chassis:
            dbchassis = get_system(session, chassis)
            if not isinstance(dbchassis, Chassis):
                raise ArgumentError("The system '%s' is not a chassis." %
                        chassis)
            if slot is None:
                raise ArgumentError("The --chassis option requires a --slot.")
            slot_force_int("slot", slot)
        elif slot is not None:
            raise ArgumentError("The --slot option requires a --chassis.")

        dbmodel = get_model(session, model)

        if dbmodel.machine_type not in ['blade', 'rackmount', 'workstation',
                'aurora_node']:
            raise ArgumentError("The add_machine command cannot add machines of type '%(type)s'.  Try 'add %(type)s'." %
                    {"type": dbmodel.machine_type})


        try:
            m = get_machine(session, machine)
            raise ArgumentError("The machine '%s' already exists"%machine)
        except NotFoundException:
            pass

        dbmachine = create_machine(session, machine, dblocation, dbmodel,
                                   cpuname, cpuvendor, cpuspeed, cpucount, memory, serial)
        if chassis:
            dbslot = session.query(ChassisSlot).filter_by(chassis=dbchassis,
                    slot_number=slot).first()
            if not dbslot:
                dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
            dbslot.machine = dbmachine
            session.save_or_update(dbslot)

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)
        return


#if __name__=='__main__':
