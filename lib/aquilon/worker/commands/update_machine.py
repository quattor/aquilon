# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq update machine`."""

import re

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import (Chassis, ChassisSlot, Model, Machine,
                                Resource, BundleResource, Share, Filesystem)
from aquilon.aqdb.types import CpuType
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.hardware_entity import update_primary_ip
from aquilon.worker.dbwrappers.interface import set_port_group, generate_ip
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.resources import (find_resource,
                                                 get_resource_holder)
from aquilon.worker.templates import (PlenaryHostData,
                                      PlenaryServiceInstanceToplevel)
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement

_disk_map_re = re.compile(r'^([^/]+)/(?:([^/]+)/)?([^/]+):([^/]+)/(?:([^/]+)/)?([^/]+)$')


def parse_remap_disk(old_vmholder, new_vmholder, remap_disk):
    result = {}
    if not remap_disk:
        return result

    maps = remap_disk.split(",")

    for map in maps:
        res = _disk_map_re.match(map)
        if not res:
            raise ArgumentError("Invalid disk backend remapping "
                                "specification: '%s'" % map)
        src_type, src_rg, src_name, dst_type, dst_rg, dst_name = res.groups()
        src_cls = Resource.polymorphic_subclass(src_type,
                                                "Invalid resource type")
        dst_cls = Resource.polymorphic_subclass(dst_type,
                                                "Invalid resource type")
        if dst_cls not in (Share, Filesystem):
            raise ArgumentError("%s is not a valid virtual disk backend "
                                "resource type." % dst_type)

        src_backend = find_resource(src_cls, old_vmholder, src_rg, src_name)
        dst_backend = find_resource(dst_cls, new_vmholder, dst_rg, dst_name)
        result[src_backend] = dst_backend

    return result


def get_metacluster(holder):
    if hasattr(holder, "metacluster"):
        return holder.metacluster

    # vmhost
    if hasattr(holder, "cluster") and holder.cluster:
        return holder.cluster.metacluster
    else:
        # TODO vlocal still has clusters, so this case not tested yet.
        return None


def update_disk_backing_stores(dbmachine, old_holder, new_holder, remap_disk):
    if not old_holder:
        old_holder = dbmachine.vm_container.holder.holder_object
    if not new_holder:
        new_holder = old_holder

    disk_mapping = parse_remap_disk(old_holder, new_holder, remap_disk)

    for dbdisk in dbmachine.disks:
        old_bstore = dbdisk.backing_store
        if isinstance(old_bstore.holder, BundleResource):
            resourcegroup = old_bstore.holder.resourcegroup.name
        else:
            resourcegroup = None

        if old_bstore in disk_mapping:
            new_bstore = disk_mapping[old_bstore]
        else:
            new_bstore = find_resource(old_bstore.__class__, new_holder,
                                       resourcegroup, old_bstore.name,
                                       error=ArgumentError)
        dbdisk.backing_store = new_bstore


def update_interface_bindings(session, logger, dbmachine, autoip):
    for dbinterface in dbmachine.interfaces:
        old_pg = dbinterface.port_group
        if not old_pg:
            continue

        old_net = old_pg.network

        # Suppress the warning about PG mismatch - we'll update the addresses
        # later
        set_port_group(session, logger, dbinterface, old_pg.name,
                       check_pg_consistency=False)
        logger.info("Updated {0:l} to use {1:l}.".format(dbinterface,
                                                         dbinterface.port_group))
        new_net = dbinterface.port_group.network

        if new_net == old_net or not autoip:
            dbinterface.check_pg_consistency(logger=logger)
            continue

        for addr in dbinterface.assignments:
            if addr.network != old_net:
                continue

            new_ip = generate_ip(session, logger, dbinterface, autoip=True,
                                 network_environment=old_net.network_environment)
            for dbdns_rec in addr.dns_records:
                dbdns_rec.network = new_net
                dbdns_rec.ip = new_ip

            old_ip = addr.ip
            addr.ip = new_ip
            addr.network = new_net
            logger.info("Changed {0:l} IP address from {1!s} to {2!s}."
                        .format(dbinterface, old_ip, new_ip))

        dbinterface.check_pg_consistency(logger=logger)


def move_vm(session, logger, dbmachine, resholder, remap_disk,
            allow_metacluster_change, autoip, plenaries):
    old_holder = dbmachine.vm_container.holder.holder_object
    if resholder:
        new_holder = resholder.holder_object
    else:
        new_holder = old_holder

    if new_holder != old_holder:
        old_mc = get_metacluster(old_holder)
        new_mc = get_metacluster(new_holder)
        if old_mc != new_mc and not allow_metacluster_change:
            raise ArgumentError("Moving VMs between metaclusters is "
                                "disabled by default.  Use the "
                                "--allow_metacluster_change option to "
                                "override.")

        plenaries.add(old_holder)
        plenaries.add(new_holder)

        dbmachine.vm_container.holder = resholder

    if new_holder != old_holder or remap_disk:
        update_disk_backing_stores(dbmachine, old_holder, new_holder, remap_disk)

    if new_holder != old_holder or autoip:
        update_interface_bindings(session, logger, dbmachine, autoip)

    if hasattr(new_holder, 'location_constraint'):
        dbmachine.location = new_holder.location_constraint
    else:
        dbmachine.location = new_holder.hardware_entity.location


class CommandUpdateMachine(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["machine"]

    def render(self, session, logger, plenaries, machine, model, vendor, serial, uuid,
               clear_uuid, chassis, slot, clearchassis, multislot, vmhost,
               cluster, metacluster, allow_metacluster_change, cpuname,
               cpuvendor, cpucount, memory, ip, autoip, uri, remap_disk,
               comments, user, justification, reason, **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)
        old_location = dbmachine.location

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbmachine)
        cm.validate()

        plenaries.add(dbmachine)
        if dbmachine.vm_container:
            plenaries.add(dbmachine.vm_container)
        if dbmachine.host:
            # Using PlenaryHostData directly, to avoid warnings if the host has
            # not been configured yet
            plenaries.add(dbmachine.host, cls=PlenaryHostData)

        if clearchassis:
            del dbmachine.chassis_slot[:]

        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            dbmachine.location = dbchassis.location
            if slot is None:
                raise ArgumentError("Option --chassis requires --slot "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)
        elif slot is not None:
            dbchassis = None
            for dbslot in dbmachine.chassis_slot:
                if dbchassis and dbslot.chassis != dbchassis:
                    raise ArgumentError("Machine in multiple chassis, please "
                                        "use --chassis argument.")
                dbchassis = dbslot.chassis
            if not dbchassis:
                raise ArgumentError("Option --slot requires --chassis "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            loc_clear_chassis = False
            for dbslot in dbmachine.chassis_slot:
                dbcl = dbslot.chassis.location
                if dbcl != dblocation:
                    if chassis or slot is not None:
                        raise ArgumentError("{0} conflicts with chassis {1!s} "
                                            "location {2}."
                                            .format(dblocation, dbslot.chassis,
                                                    dbcl))
                    else:
                        loc_clear_chassis = True
            if loc_clear_chassis:
                del dbmachine.chassis_slot[:]
            dbmachine.location = dblocation

        if model:
            # If overriding model, should probably overwrite default
            # machine specs as well.
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)
            if not dbmodel.model_type.isMachineType():
                raise ArgumentError("The update_machine command cannot update "
                                    "machines of type %s." %
                                    dbmodel.model_type)
            # We probably could do this by forcing either cluster or
            # location data to be available as appropriate, but really?
            # Failing seems reasonable.
            if dbmodel.model_type != dbmachine.model.model_type and \
                (dbmodel.model_type.isVirtualMachineType() or
                 dbmachine.model.model_type.isVirtualMachineType()):
                raise ArgumentError("Cannot change machine from %s to %s." %
                                    (dbmachine.model.model_type,
                                     dbmodel.model_type))

            old_nic_model = dbmachine.model.nic_model
            new_nic_model = dbmodel.nic_model
            if old_nic_model != new_nic_model:
                for iface in dbmachine.interfaces:
                    if iface.model == old_nic_model:
                        iface.model = new_nic_model

            dbmachine.model = dbmodel

        if cpuname or cpuvendor:
            dbcpu = Model.get_unique(session, name=cpuname, vendor=cpuvendor,
                                     model_type=CpuType.Cpu, compel=True)
            dbmachine.cpu_model = dbcpu

        if cpucount is not None:
            dbmachine.cpu_quantity = cpucount
        if memory is not None:
            dbmachine.memory = memory
        if serial is not None:
            dbmachine.serial_no = serial
        if comments is not None:
            dbmachine.comments = comments

        if uuid:
            q = session.query(Machine)
            q = q.filter_by(uuid=uuid)
            existing = q.first()
            if existing:
                raise ArgumentError("{0} is already using UUID {1!s}."
                                    .format(existing, uuid))
            dbmachine.uuid = uuid
        elif clear_uuid:
            dbmachine.uuid = None

        if uri and not dbmachine.model.model_type.isVirtualMachineType():
            raise ArgumentError("URI can be specified only for virtual "
                                "machines and the model's type is %s" %
                                dbmachine.model.model_type)

        if uri is not None:
            dbmachine.uri = uri

        # FIXME: For now, if a machine has its interface(s) in a portgroup
        # this command will need to be followed by an update_interface to
        # re-evaluate the portgroup for overflow.
        # It would be better to have --pg and --autopg options to let it
        # happen at this point.
        if cluster or vmhost or metacluster:
            if not dbmachine.vm_container:
                raise ArgumentError("Cannot convert a physical machine to "
                                    "virtual.")

            resholder = get_resource_holder(session, logger, hostname=vmhost,
                                            cluster=cluster,
                                            metacluster=metacluster,
                                            compel=False)
            move_vm(session, logger, dbmachine, resholder, remap_disk,
                    allow_metacluster_change, autoip, plenaries)
        elif remap_disk:
            update_disk_backing_stores(dbmachine, None, None, remap_disk)

        if ip:
            if dbmachine.host:
                for srv in dbmachine.host.services_provided:
                    si = srv.service_instance
                    plenaries.add(si, cls=PlenaryServiceInstanceToplevel)
            update_primary_ip(session, logger, dbmachine, ip)

        if dbmachine.location != old_location and dbmachine.host:
            for vm in dbmachine.host.virtual_machines:
                plenaries.add(vm)
                vm.location = dbmachine.location

        session.flush()

        # Check if the changed parameters still meet cluster capacity
        # requiremets
        if dbmachine.cluster:
            dbmachine.cluster.validate()
            if allow_metacluster_change and dbmachine.cluster.metacluster:
                dbmachine.cluster.metacluster.validate()
        if dbmachine.host and dbmachine.host.cluster:
            dbmachine.host.cluster.validate()

        for dbinterface in dbmachine.interfaces:
            dbinterface.check_pg_consistency(logger=logger)

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        with plenaries.transaction():
            dsdb_runner = DSDBRunner(logger=logger)
            if dbmachine.host and dbmachine.host.archetype.name == 'aurora':
                try:
                    dsdb_runner.show_host(dbmachine.fqdn)
                except ProcessException as e:
                    raise ArgumentError("Could not find host in DSDB: "
                                        "%s" % e)
            else:
                dsdb_runner.update_host(dbmachine, oldinfo)
                dsdb_runner.commit_or_rollback("Could not update machine in DSDB")

        return

    def adjust_slot(self, session, logger,
                    dbmachine, dbchassis, slot, multislot):
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
            slots = ", ".join(str(dbslot.slot_number) for dbslot in
                              dbmachine.chassis_slot)
            logger.info("Clearing {0:l} out of {1:l} slot(s) "
                        "{2}".format(dbmachine, dbchassis, slots))
            del dbmachine.chassis_slot[:]
        q = session.query(ChassisSlot)
        q = q.filter_by(chassis=dbchassis, slot_number=slot)
        dbslot = q.first()
        if dbslot:
            if dbslot.machine:
                raise ArgumentError("{0} slot {1} already has machine "
                                    "{2}.".format(dbchassis, slot,
                                                  dbslot.machine.label))
        else:
            dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
        dbmachine.chassis_slot.append(dbslot)

        return
