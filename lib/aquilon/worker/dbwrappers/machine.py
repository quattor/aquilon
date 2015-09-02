# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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
from aquilon.aqdb.types import CpuType
from aquilon.aqdb.model import (Model, LocalDisk, Machine, VirtualDisk, Share,
                                Filesystem)
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.dbwrappers.resources import find_resource


def create_machine(session, machine, dblocation, dbmodel, cpuname=None,
                   cpuvendor=None, cpucount=None, memory=None, serial=None,
                   comments=None):
    if cpuname:
        dbcpu = Model.get_unique(session, name=cpuname, vendor=cpuvendor,
                                 model_type=CpuType.Cpu, compel=True)
    else:
        if not dbmodel.machine_specs:
            raise ArgumentError("Model %s does not have machine specification "
                                "defaults, please specify --cpuname and "
                                "--cpuvendor." % dbmodel.name)
        dbcpu = dbmodel.machine_specs.cpu_model

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
                        cpu_model=dbcpu, cpu_quantity=cpucount, memory=memory,
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


def add_disk(dbmachine, disk, controller, share=None, filesystem=None,
             resourcegroup=None, address=None, size=None, boot=None,
             snapshot=None, wwn=None, bus_address=None, iops_limit=None,
             comments=None):
    if controller not in controller_types:
        raise ArgumentError("%s is not a valid controller type, use one "
                            "of: %s." %
                            (controller, ", ".join(sorted(controller_types))))

    for dbdisk in dbmachine.disks:
        if dbdisk.device_name == disk:
            raise ArgumentError("{0} already has a disk named {1!s}."
                                .format(dbmachine, dbdisk.device_name))
        if dbdisk.bootable:
            if boot is None:
                boot = False
            elif boot:
                raise ArgumentError("{0} already has a boot disk."
                                    .format(dbmachine))

    if boot is None:
        # Backward compatibility: "sda"/"c0d0" is bootable, except if there
        # is already a boot disk
        boot = (disk == "sda" or disk == "c0d0")

    extra_params = {}
    if share or filesystem:
        cls = VirtualDisk
        if not dbmachine.vm_container:
            raise ArgumentError("{0} is not a virtual machine, it is not "
                                "possible to define a virtual disk."
                                .format(dbmachine))

        if share:
            res_cls = Share
            res_name = share
        else:
            res_cls = Filesystem
            res_name = filesystem

        dbres = find_resource(res_cls,
                              dbmachine.vm_container.holder.holder_object,
                              resourcegroup, res_name)
        extra_params["backing_store"] = dbres
        extra_params["snapshotable"] = snapshot
        extra_params["iops_limit"] = iops_limit
    else:
        cls = LocalDisk

    dbdisk = cls(device_name=disk, controller_type=controller,
                 capacity=size, bootable=boot, wwn=wwn, address=address,
                 bus_address=bus_address, comments=comments, **extra_params)

    dbmachine.disks.append(dbdisk)
