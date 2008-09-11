#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add machine`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import (ArgumentError, NotFoundException,
                                 UnimplementedError)
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.aqdb.hw.chassis_slot import ChassisSlot
from aquilon.aqdb.hw.cpu import Cpu


class CommandUpdateMachine(BrokerCommand):

    required_parameters = ["machine"]

    @add_transaction
    @az_check
    def render(self, session, machine, model, serial, chassis, slot,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            user, **arguments):
        dbmachine = get_machine(session, machine)

        if chassis:
            dbchassis = get_system(session, chassis, Chassis, 'Chassis')
            dbmachine.location = dbchassis.chassis_hw.location
            if slot is None:
                raise ArgumentError("Option --chassis requires --slot information")
            slot = force_int("slot", slot)
            dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot,
                                 machine=dbmachine)
            session.save(dbslot)
        elif slot:
            slot = force_int("slot", slot)
            if not dbmachine.chassis_slot:
                raise ArgumentError("Option --slot requires --chassis information")
            for dbslot in dbmachine.chassis_slot:
                dbslot.slot_number = slot
                session.update(dbslot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            for dbslot in dbmachine.chassis_slot:
                dbcl = dslot.chassis.chassis_hw.location
                if dbcl != dblocation:
                    if chassis or slot is not None:
                        raise ArgumentError("Location %s %s conflicts with chassis %s location %s %s" % (
                                            dblocation.location_type,
                                            dblocation.name,
                                            dbslot.chassis.fqdn,
                                            dbcl.location_type, dbcl.name))
                    else:
                        session.delete(dbslot)
            dbmachine.location = dblocation

        if model:
            # If overriding model, should probably overwrite default
            # machine specs as well.
            dbmodel = get_model(session, model)
            if dbmodel.machine_type not in ['blade', 'rackmount', 'workstation',
                    'aurora_node']:
                raise ArgumentError("The update_machine command cannot update machines of type '%(type)s'." %
                        {"type": dbmodel.machine_type})
            dbmachine.model = dbmodel

        if cpuname and cpuvendor and cpuspeed:
            cpuspeed = force_int("cpuspeed", cpuspeed)
            q = session.query(Cpu).filter_by(name=cpuname, speed=cpuspeed)
            q = q.join('vendor').filter_by(name=cpuvendor)
            try:
                dbcpu = q.one()
            except InvalidRequestError, e:
                raise ArgumentError("Could not uniquely identify a CPU with name %s, speed %s, and vendor %s: %s" %
                        (cpuname, cpuspeed, cpuvendor, e))
            dbmachine.cpu = dbcpu
        elif cpuname or cpuvendor or cpuspeed:
            raise UnimplementedError("Can only update a machine with an exact cpu (--cpuname, --cpuvendor, and --cpuspeed).")

        if cpucount:
            cpucount = force_int("cpucount", cpucount)
            dbmachine.cpu_quantity = cpucount
        if memory:
            memory = force_int("memory", memory)
            dbmachine.memory=memory
        if serial:
            dbmachine.serial_no=serial

        session.update(dbmachine)
        session.flush()

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        if dbmachine.host:
            # XXX: May need to reconfigure.
            pass

        return


#if __name__=='__main__':
