# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wrapper to make getting a machine simpler."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cpu, LocalDisk, Machine


def create_machine(session, machine, dblocation, dbmodel, cpuname=None,
                   cpuvendor=None, cpuspeed=None, cpucount=None, memory=None,
                   serial=None, comments=None):

    # Figure out a CPU...
    dbcpu = None
    if not (cpuname or cpuvendor or cpuspeed is not None):
        if not dbmodel.machine_specs:
            raise ArgumentError("Model %s does not have machine specification "
                                "defaults, please specify --cpuvendor, "
                                "--cpuname, and --cpuspeed." % dbmodel.name)
        dbcpu = dbmodel.machine_specs.cpu
    else:
        # Was there enough on the command line to specify one?
        q = session.query(Cpu)
        if cpuname:
            q = q.filter(Cpu.name.like(cpuname.lower() + '%'))
        if cpuspeed is not None:
            q = q.filter_by(speed=cpuspeed)
        if cpuvendor:
            q = q.join('vendor').filter_by(name=cpuvendor.lower())
        cpulist = q.all()
        if not cpulist:
            raise ArgumentError("Could not find a CPU with the given "
                                "attributes.")
        if len(cpulist) == 1:
            # Found it exactly.
            dbcpu = cpulist[0]
        elif dbmodel.machine_specs:
            # Not exact, but see if the specs match the default.
            dbcpu = dbmodel.machine_specs.cpu
            if ((cpuname and not dbcpu.name.startswith(cpuname.lower()))
                    or (cpuspeed is not None and dbcpu.speed != cpuspeed)
                    or (cpuvendor and
                        dbcpu.vendor.name != cpuvendor.lower())):
                raise ArgumentError("Could not uniquely identify a CPU with "
                                    "the attributes given.")
        else:
            raise ArgumentError("Could not uniquely identify a CPU with the "
                                "attributes given.")

    if cpucount is None:
        if dbmodel.machine_specs:
            cpucount = dbmodel.machine_specs.cpu_quantity
        else:
            raise ArgumentError("Model %s does not have machine specification "
                                "defaults, please specify --cpucount." %
                                dbmodel.name)

    if memory is None:
        if dbmodel.machine_specs:
            memory = dbmodel.machine_specs.memory
        else:
            raise ArgumentError("Model %s does not have machine specification "
                                "defaults, please specify --memory (in MB)." %
                                dbmodel.name)

    dbmachine = Machine(location=dblocation, model=dbmodel, label=machine,
                        cpu=dbcpu, cpu_quantity=cpucount, memory=memory,
                        serial_no=serial, comments=comments)
    session.add(dbmachine)

    if dbmodel.machine_specs and not dbmodel.model_type.isAuroraNode() \
       and dbmodel.machine_specs.disk_type == 'local':
        specs = dbmodel.machine_specs
        dbdisk = LocalDisk(machine=dbmachine, device_name=specs.disk_name,
                           controller_type=specs.controller_type,
                           capacity=specs.disk_capacity, bootable=True)
        session.add(dbdisk)

    session.flush()
    return dbmachine
