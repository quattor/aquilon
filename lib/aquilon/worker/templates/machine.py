#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
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
"""Any work by the broker to write out (or read in?) templates lives here."""


import logging

from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import (Machine, LocalDisk, VirtualDisk, Share,
                                Filesystem)
from aquilon.worker.locks import CompileKey, NoLockKey
from aquilon.worker.templates import (Plenary, StructurePlenary,
                                      add_location_info)
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include, PanMetric)
from aquilon.utils import nlist_key_re

LOGGER = logging.getLogger(__name__)


class PlenaryMachineInfo(StructurePlenary):
    prefix = "machine"

    @classmethod
    def template_name(cls, dbmachine):
        loc = dbmachine.location
        return "%s/%s/%s/%s/%s" % (cls.prefix, loc.continent.name,
                                   loc.building, loc.rack, dbmachine.label)

    def __init__(self, dbobj, **kwargs):
        super(PlenaryMachineInfo, self).__init__(dbobj, **kwargs)

        # Use the hardware label for debug logs, not the primary name
        self.debug_name = dbobj.label

    def get_key(self, exclusive=True):
        if not exclusive:
            # CompileKey() does not support shared mode
            raise InternalError("Shared locks are not implemented for machine "
                                "plenaries.")

        # Need a compile key if:
        # - There is a host attached.
        # - This is a virtual machine in a container.
        keylist = [NoLockKey(logger=self.logger)]
        if not inspect(self.dbobj).deleted:
            if self.dbobj.host:
                plenary = Plenary.get_plenary(self.dbobj.host,
                                              logger=self.logger)
                keylist.append(plenary.get_key())
            if self.dbobj.vm_container:
                plenary = Plenary.get_plenary(self.dbobj.vm_container,
                                              logger=self.logger)
                keylist.append(plenary.get_key())
        return CompileKey.merge(keylist)

    def body(self, lines):
        ram = [StructureTemplate("hardware/ram/generic",
                                 {"size": PanMetric(self.dbobj.memory, "MB")})]
        cpu = StructureTemplate("hardware/cpu/%s/%s" %
                                (self.dbobj.cpu_model.vendor.name,
                                 self.dbobj.cpu_model.name))
        cpus = [cpu] * self.dbobj.cpu_quantity

        disks = {}
        for disk in self.dbobj.disks:
            devname = disk.device_name
            params = {"capacity": PanMetric(disk.capacity, "GB"),
                      "interface": disk.controller_type}
            if disk.bootable:
                params["boot"] = True
            if disk.wwn:
                params["wwn"] = disk.wwn
            if disk.address:
                params["address"] = disk.address
            if disk.bus_address:
                params["bus"] = disk.bus_address

            if hasattr(disk, "snapshotable") and disk.snapshotable is not None:
                params["snapshot"] = disk.snapshotable

            if hasattr(disk, "iops_limit") and disk.iops_limit is not None:
                params["iopslimit"] = disk.iops_limit

            if disk.disk_tech:
                params["disk_tech"] = disk.disk_tech
            if disk.usage:
                params["usage"] = disk.usage
            if disk.diskgroup_key:
                params["diskgroup_key"] = disk.diskgroup_key
            if disk.model_key:
                params["model_key"] = disk.model_key

            if (hasattr(disk, "vsan_policy_key") and
                    disk.vsan_policy_key is not None):
                params["vsan_policy_key"] = disk.vsan_policy_key

            if isinstance(disk, LocalDisk):
                tpl = StructureTemplate("hardware/harddisk/generic/%s" %
                                        disk.controller_type, params)

                if disk.controller_type == 'cciss':
                    devname = "cciss/" + devname
            elif isinstance(disk, VirtualDisk):
                dbres = disk.backing_store

                params["path"] = "%s/%s.vmdk" % (self.dbobj.label, disk.device_name)
                params["address"] = disk.address

                if isinstance(dbres, Share):
                    params["sharename"] = dbres.name
                    params["server"] = dbres.server
                    params["mountpoint"] = dbres.mount
                elif isinstance(dbres, Filesystem):
                    params["filesystemname"] = dbres.name
                    params["mountpoint"] = dbres.mountpoint

                tpl = params

            disks[devname] = tpl

        managers = {}
        interfaces = {}
        for interface in self.dbobj.interfaces:
            path = "hardware/nic/%s/%s" % (interface.model.vendor,
                                           interface.model)
            if interface.interface_type == 'public':
                ifinfo = {}
                if interface.mac:
                    ifinfo["hwaddr"] = interface.mac
                if interface.port_group:
                    ifinfo["port_group"] = interface.port_group.name
                elif interface.port_group_name:
                    ifinfo["port_group"] = interface.port_group_name
                if interface.bootable:
                    ifinfo["boot"] = interface.bootable
                if interface.bus_address:
                    ifinfo["bus"] = interface.bus_address
                interfaces[interface.name] = StructureTemplate(path, ifinfo)
            elif interface.interface_type == 'management':
                has_addr = False
                for addr in interface.assignments:
                    has_addr = True
                    manager = {"hwaddr": interface.mac}
                    if addr.fqdns:
                        manager["fqdn"] = addr.fqdns[0]
                    managers[addr.logical_name] = manager
                if not has_addr:
                    managers[interface.name] = {"hwaddr": interface.mac}
            elif interface.interface_type == 'bonding':
                # Bonding interfaces need an entry under /hardware/cards/nic
                # only if the MAC address has been explicitely set
                if interface.mac:
                    ifinfo = {"hwaddr": interface.mac}
                    interfaces[interface.name] = StructureTemplate(path, ifinfo)

        # Firstly, location
        add_location_info(lines, self.dbobj.location)
        pan_assign(lines, "location", self.dbobj.location.sysloc())

        # And a chassis location?
        if self.dbobj.chassis_slot:
            slot = self.dbobj.chassis_slot[0]
            pan_assign(lines, "chassis", slot.chassis.fqdn)
            pan_assign(lines, "slot", slot.slot_number)

        # Now describe the hardware
        lines.append("")
        if self.dbobj.serial_no:
            pan_assign(lines, "serialnumber", self.dbobj.serial_no)
        pan_assign(lines, "nodename", self.dbobj.label)
        pan_include(lines, "hardware/machine/%s/%s" %
                    (self.dbobj.model.vendor.name, self.dbobj.model.name))

        lines.append("")
        pan_assign(lines, "ram", ram)
        pan_assign(lines, "cpu", cpus)
        for name in sorted(disks):
            pan_assign(lines, "harddisks/{%s}" % name, disks[name])
        for name in sorted(interfaces):
            # This is ugly. We can't blindly escape, because that would affect
            # e.g. VLAN interfaces. Calling unescape() for a non-escaped VLAN
            # interface name is safe though, so we can hopefully get rid of this
            # once the templates are changed to call unescape().
            if nlist_key_re.match(name):
                pan_assign(lines, "cards/nic/%s" % name, interfaces[name])
            else:
                pan_assign(lines, "cards/nic/{%s}" % name, interfaces[name])

        # /hardware/console/preferred must be set, so we can't assign to
        # "/console" directly
        for manager in sorted(managers):
            pan_assign(lines, "console/%s" % manager, managers[manager])
        for port in self.dbobj.consoles:
            console_port = self.dbobj.consoles[port]
            pan_assign(lines, "console/remote/%s/fqdn" % console_port.client_port,
                       console_port.console_server)
            pan_assign(lines, "console/remote/%s/port" % console_port.client_port,
                       console_port.port_number)

        if self.dbobj.uri:
            pan_assign(lines, "uri", self.dbobj.uri)
        if self.dbobj.uuid:
            pan_assign(lines, "uuid", self.dbobj.uuid)

Plenary.handlers[Machine] = PlenaryMachineInfo
