#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a machine simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.hw.machine import Machine
from aquilon.aqdb.hw.cpu import Cpu
from aquilon.aqdb.hw.disk import Disk
from aquilon.server.broker import force_int


def get_machine(session, machine):
    try:
        dbmachine = session.query(Machine).filter_by(name=machine).one()
    except InvalidRequestError, e:
        raise NotFoundException("Machine %s not found: %s" % (machine, e))
    return dbmachine

def create_machine(session, machine, dblocation, dbmodel,
        cpuname, cpuvendor, cpuspeed, cpucount, memory, serial):
    if cpuspeed is not None:
        cpuspeed = force_int("cpuspeed", cpuspeed)

    # Figure out a CPU...
    dbcpu = None
    if not (cpuname or cpuspeed or cpuvendor):
        if not dbmodel.machine_specs:
            ArgumentError("Model %s does not have machine specification defaults, please specify --cpuvendor, --cpuname, and --cpuspeed." %
                    dbmodel.name)
        dbcpu = dbmodel.machine_specs.cpu
    else:
        # Was there enough on the command line to specify one?
        q = session.query(Cpu)
        if cpuname:
            q = q.filter(Cpu.name.like(cpuname.lower() + '%'))
        if cpuspeed:
            q = q.filter_by(speed=cpuspeed)
        if cpuvendor:
            q = q.join('vendor').filter_by(name=cpuvendor.lower())
        cpulist = q.all()
        if not cpulist:
            raise ArgumentError("Could not find a cpu with the given attributes.")
        if len(cpulist) == 1:
            # Found it exactly.
            dbcpu = cpulist[0]
        elif dbmodel.machine_specs:
            # Not exact, but see if the specs match the default.
            dbcpu = dbmodel.machine_specs.cpu
            if ((cpuname and not dbcpu.name.startswith(cpuname.lower))
                    or (cpuspeed and dbcpu.speed != cpuspeed)
                    or (cpuvendor and
                        dbcpu.vendor.name != cpuvendor.lower())):
                raise ArgumentError("Could not uniquely identify a cpu with the attributes given.")
        else:
            raise ArgumentError("Could not uniquely identify a cpu with the attributes given.")
    
    if cpucount is None:
        if dbmodel.machine_specs:
            cpucount = dbmodel.machine_specs.cpu_quantity
        else:
            ArgumentError("Model %s does not have machine specification defaults, please specify --cpucount." %
                    model)
    else:
        cpucount = force_int("cpucount", cpucount)

    if memory is None:
        if dbmodel.machine_specs:
            memory = dbmodel.machine_specs.memory
        else:
            ArgumentError("Model %s does not have machine specification defaults, please specify --memory (in MB)." %
                    model)
    else:
        memory = force_int("memory", memory)

    dbmachine = Machine(location=dblocation, model=dbmodel, name=machine,
            cpu=dbcpu, cpu_quantity=cpucount, memory=memory, serial_no=serial)
    session.save(dbmachine)

    if dbmodel.machine_specs:
        dbdisk = Disk(machine=dbmachine,
                disk_type=dbmodel.machine_specs.disk_type,
                capacity=dbmodel.machine_specs.disk_capacity)
        session.save(dbdisk)

    session.flush()
    return dbmachine


#if __name__=='__main__':
