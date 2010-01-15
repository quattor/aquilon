# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Wrapper to make getting a machine simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Cpu, LocalDisk, Machine
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
            raise ArgumentError("Model %s does not have machine specification defaults, please specify --cpuvendor, --cpuname, and --cpuspeed." %
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
            if ((cpuname and not dbcpu.name.startswith(cpuname.lower()))
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
            raise ArgumentError("Model %s does not have machine specification defaults, please specify --cpucount." %
                    dbmodel.name)
    else:
        cpucount = force_int("cpucount", cpucount)

    if memory is None:
        if dbmodel.machine_specs:
            memory = dbmodel.machine_specs.memory
        else:
            raise ArgumentError("Model %s does not have machine specification defaults, please specify --memory (in MB)." %
                    dbmodel.name)
    else:
        memory = force_int("memory", memory)

    dbmachine = Machine(location=dblocation, model=dbmodel, name=machine,
            cpu=dbcpu, cpu_quantity=cpucount, memory=memory, serial_no=serial)
    session.add(dbmachine)

    if dbmodel.machine_specs and dbmodel.machine_type != 'aurora_node' \
       and dbmodel.machine_specs.disk_type == 'local':
        # FIXME: Look up an appropriate default device name based on
        # controller_type.
        dbdisk = LocalDisk(machine=dbmachine, device_name='sda',
                controller_type=dbmodel.machine_specs.controller_type,
                capacity=dbmodel.machine_specs.disk_capacity)
        session.add(dbdisk)

    session.flush()
    return dbmachine
