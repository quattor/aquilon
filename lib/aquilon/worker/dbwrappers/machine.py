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

import json
import jsonschema
import os.path

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.types import CpuType
from aquilon.aqdb.model import (Model, LocalDisk, VirtualDisk, Machine,
                                VirtualMachine, Share, Filesystem)
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 generate_mac, set_port_group)
from aquilon.worker.dbwrappers.resources import find_resource
from aquilon.utils import force_mac


def validate_recipe(config, recipe):
    srcdir = config.get("broker", "srcdir")
    schema_dir = os.path.join(srcdir, "etc", "schema")
    schema_file = os.path.join(schema_dir, "machine_recipe.json")
    resolver = jsonschema.RefResolver("file://" + schema_file, "machine_recipe.json")
    format_checker = jsonschema.FormatChecker()

    try:
        with open(schema_file) as fp:
            schema = json.load(fp)
        jsonschema.Draft4Validator.check_schema(schema)
    except Exception as err:
        raise AquilonError("Failed to load %s: %s" % (schema_file, err))

    try:
        jsonschema.validate(recipe, schema, resolver=resolver,
                            format_checker=format_checker)
    except jsonschema.ValidationError as err:
        raise ArgumentError("recipe validation failed: %s" % err)

    # Type conversions not covered by the schema
    if "interfaces" in recipe:
        for iface, params in recipe["interfaces"].items():
            if "mac" in params:
                params["mac"] = force_mac("MAC address of " + iface,
                                          params["mac"])


def create_machine(config, session, logger, machine, dblocation, dbmodel,
                   recipe=None, cpuname=None, cpuvendor=None, cpucount=None,
                   memory=None, serial=None, uri=None, vmholder=None,
                   comments=None):
    if recipe is None:
        recipe = {}
    else:
        validate_recipe(config, recipe)

    if cpuname is None:
        cpuname = recipe.get("cpuname", None)
        cpuvendor = recipe.get("cpuvendor", None)
    if cpuname:
        dbcpu = Model.get_unique(session, name=cpuname, vendor=cpuvendor,
                                 model_type=CpuType.Cpu, compel=True)
    else:
        if not dbmodel.machine_specs:
            raise ArgumentError("Model %s does not have machine specification "
                                "defaults, please specify --cpuvendor, "
                                "--cpuname, or --cpuspeed." % dbmodel.name)
        dbcpu = dbmodel.machine_specs.cpu_model

    if cpucount is None:
        cpucount = recipe.get("cpucount", None)
    if cpucount is None:
        if dbmodel.machine_specs:
            cpucount = dbmodel.machine_specs.cpu_quantity
        else:
            raise ArgumentError("Model %s does not have machine specification "
                                "defaults, please specify --cpucount." %
                                dbmodel.name)

    if memory is None:
        memory = recipe.get("memory", None)
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
    # Initialize the collections to prevent loading them from the DB
    dbmachine.disks = []
    dbmachine.interfaces = []

    if uri is None:
        uri = recipe.get("uri", None)
    if uri:
        if not dbmodel.model_type.isVirtualAppliance():
            raise ArgumentError("URI can be specified only for virtual "
                                "appliances and the model's type is %s." %
                                dbmodel.model_type)
        dbmachine.uri = uri

    session.add(dbmachine)

    if dbmodel.machine_specs and not dbmodel.model_type.isAuroraNode() \
       and dbmodel.machine_specs.disk_type == 'local':
        specs = dbmodel.machine_specs
        dbdisk = LocalDisk(machine=dbmachine, device_name=specs.disk_name,
                           controller_type=specs.controller_type,
                           capacity=specs.disk_capacity, bootable=True)
        session.add(dbdisk)

    # The .vmholder attribure needs to be set before virtual disks can be added
    if vmholder:
        dbvm = VirtualMachine(machine=dbmachine, name=dbmachine.label,
                              holder=vmholder)
        session.add(dbvm)
        if hasattr(vmholder.holder_object, "validate") and \
           callable(vmholder.holder_object.validate):
            vmholder.holder_object.validate()

    if "disks" in recipe:
        for disk_name, disk_params in recipe["disks"].items():
            add_disk(dbmachine, disk_name, **disk_params)

    if "interfaces" in recipe:
        for iface_name, iface_params in recipe["interfaces"].items():
            # Due to locking order, automac handling must come before autopg
            add_interface(config, session, logger, dbmachine, iface_name,
                          **iface_params)

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


def add_interface(config, session, logger, dbmachine, interface, mac=None,
                  automac=None, pg=None, autopg=None, vendor=None, model=None,
                  iftype=None, boot=None, bus_address=None, comments=None):
    if not iftype:
        iftype = 'public'
        management_types = ['bmc', 'ilo', 'ipmi', 'mgmt']
        for mtype in management_types:
            if interface.startswith(mtype):
                iftype = 'management'
                break

        if interface.startswith("bond"):
            iftype = 'bonding'
        elif interface.startswith("br"):
            iftype = 'bridge'

        # Test it last, VLANs can be added on top of almost anything
        if '.' in interface:
            iftype = 'vlan'

    if iftype == "oa" or iftype == "loopback":
        raise ArgumentError("Interface type '%s' is not valid for "
                            "machines." % iftype)

    if automac:
        mac = generate_mac(session, config, dbmachine)

    if autopg and not pg:
        pg = "user"

    if boot is None and iftype == 'public':
        if interface == 'eth0':
            boot = True
        else:
            boot = False

    dbinterface = get_or_create_interface(session, dbmachine, name=interface,
                                          vendor=vendor, model=model,
                                          bus_address=bus_address,
                                          interface_type=iftype, mac=mac,
                                          bootable=boot, comments=comments,
                                          preclude=True)

    if automac:
        logger.info("Selected MAC address {0!s} for {1:l}."
                    .format(mac, dbinterface))
    if pg:
        set_port_group(session, logger, dbinterface, pg)
    return dbinterface
