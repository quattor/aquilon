# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add machine`."""


from sqlalchemy.exceptions import InvalidRequestError
from twisted.python import log

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
               clearchassis, multislot,
               cpuname, cpuvendor, cpuspeed, cpucount, memory,
               user, **arguments):
        dbmachine = get_machine(session, machine)

        if clearchassis:
            for dbslot in dbmachine.chassis_slot:
                dbslot.machine = None
                session.update(dbslot)
            session.flush()
            session.refresh(dbmachine)

        if chassis:
            dbchassis = get_system(session, chassis, Chassis, 'Chassis')
            dbmachine.location = dbchassis.chassis_hw.location
            if slot is None:
                raise ArgumentError("Option --chassis requires --slot information")
            slot = force_int("slot", slot)
            self.adjust_slot(session, dbmachine, dbchassis, slot, multislot)
        elif slot:
            dbchassis = None
            for dbslot in dbmachine.chassis_slot:
                if dbchassis and dbslot.chassis != dbchassis:
                    raise ArgumentError("Machine in multiple chassis, please "
                                        "use --chassis argument")
                dbchassis = dbslot.chassis
            if not dbchassis:
                raise ArgumentError("Option --slot requires --chassis "
                                    "information")
            slot = force_int("slot", slot)
            self.adjust_slot(session, dbmachine, dbchassis, slot, multislot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            for dbslot in dbmachine.chassis_slot:
                dbcl = dbslot.chassis.chassis_hw.location
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
        session.refresh(dbmachine)

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

    def adjust_slot(self, session, dbmachine, dbchassis, slot, multislot):
        for dbslot in dbmachine.chassis_slot:
            # This update is a noop, ignore.
            # Technically, this could be a request to trim the list down
            # to just this one slot - in that case --clearchassis will be
            # required.
            if dbslot.chassis == dbchassis and dbslot.slot_number == slot:
                return
        if len(dbmachine.chassis_slot) > 1 and not multislot:
            raise ArgumentError("Use --multislot to support a machine in more "
                                "than one slot, or --clearchassis to remove "
                                "current chassis slot information.")
        if not multislot:
            for dbslot in dbmachine.chassis_slot:
                log.msg("Clearing machine %s out of chassis %s slot %d" %
                        (dbmachine.name, dbslot.chassis.fqdn,
                         dbslot.slot_number))
                dbslot.machine = None
        q = session.query(ChassisSlot)
        q = q.filter_by(chassis=dbchassis, slot_number=slot)
        dbslot = q.first()
        if dbslot:
            if dbslot.machine:
                raise ArgumentError("Chassis %s slot %d already has machine "
                                    "%s" % (dbchassis.fqdn, slot,
                                            dbslot.machine.name))
            dbslot.machine = dbmachine
            session.update(dbslot)
        else:
            dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot,
                                 machine=dbmachine)
            session.save(dbslot)
        return


