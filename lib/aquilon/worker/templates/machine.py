# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from aquilon.aqdb.model import Machine
from aquilon.worker.locks import CompileKey, NoLockKey
from aquilon.worker.templates import (Plenary, StructurePlenary,
                                      add_location_info)
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include, PanMetric)

LOGGER = logging.getLogger(__name__)


class PlenaryMachineInfo(StructurePlenary):

    @classmethod
    def template_name(cls, dbmachine):
        loc = dbmachine.location
        return "machine/%s/%s/%s/%s" % (loc.hub.fullname.lower(), loc.building,
                                        loc.rack, dbmachine.label)

    def get_key(self):
        host = self.dbobj.host
        container = self.dbobj.vm_container
        # Need a compile key if:
        # - There is a host attached.
        # - This is a virtual machine in a container.
        if not host and not container:
            return NoLockKey(logger=self.logger)
        # We have at least host or container, maybe both...
        if host:
            # PlenaryHost is actually a PlenaryCollection... can't call
            # get_key() directly, so using get_remove_key().
            ph = Plenary.get_plenary(host, logger=self.logger)
            host_key = ph.get_remove_key()
        if container:
            pc = Plenary.get_plenary(container, self.logger)
            container_key = pc.get_key()
        if not container:
            return host_key
        if not host:
            return container_key
        return CompileKey.merge([host_key, container_key])

    def body(self, lines):
        ram = [StructureTemplate("hardware/ram/generic",
                                 {"size": PanMetric(self.dbobj.memory, "MB")})]
        cpus = []
        for cpu_num in range(self.dbobj.cpu_quantity):
            cpu = StructureTemplate("hardware/cpu/%s/%s" %
                                    (self.dbobj.cpu.vendor.name,
                                     self.dbobj.cpu.name))
            cpus.append(cpu)

        disks = {}
        for disk in self.dbobj.disks:
            devname = disk.device_name
            params = {"capacity": PanMetric(disk.capacity, "GB"),
                      "interface": disk.controller_type}
            if disk.bootable:
                params["boot"] = True

            if hasattr(disk, "snapshotable") and disk.snapshotable is not None:
                params["snapshot"] = disk.snapshotable

            if disk.disk_type == 'local':
                tpl = StructureTemplate("hardware/harddisk/generic/%s" %
                                        disk.controller_type, params)

                if disk.controller_type == 'cciss':
                    devname = "cciss/" + devname
            elif disk.disk_type == 'virtual_disk':
                share = disk.share

                params["path"] = "%s/%s.vmdk" % (self.dbobj.label, disk.device_name)
                params["address"] = disk.address
                params["sharename"] = share.name
                params["server"] = share.server
                params["mountpoint"] = share.mount

                tpl = params

            elif disk.disk_type == 'virtual_localdisk':
                filesystem = disk.filesystem

                params["path"] = "%s/%s.vmdk" % (self.dbobj.label, disk.device_name)
                params["address"] = disk.address
                params["filesystemname"] = filesystem.name
                params["mountpoint"] = filesystem.mountpoint

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
                    ifinfo["port_group"] = interface.port_group
                if interface.bootable:
                    ifinfo["boot"] = interface.bootable
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

        dns_search_domains = []
        parents = self.dbobj.location.parents[:]
        parents.append(self.dbobj.location)
        parents.reverse()
        for parent in parents:
            # Filter out duplicates
            extra_domains = [map.dns_domain.name
                             for map in parent.dns_maps
                             if map.dns_domain.name not in dns_search_domains]
            dns_search_domains.extend(extra_domains)

        if dns_search_domains:
            pan_assign(lines, "sysloc/dns_search_domains", dns_search_domains)

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
        for name in sorted(disks.keys()):
            pan_assign(lines, "harddisks/{%s}" % name, disks[name])
        if interfaces:
            pan_assign(lines, "cards/nic", interfaces)

        # /hardware/console/preferred must be set, so we can't assign to
        # "/console" directly
        for manager in sorted(managers.keys()):
            pan_assign(lines, "console/%s" % manager, managers[manager])

Plenary.handlers[Machine] = PlenaryMachineInfo


def machine_plenary_will_move(old, new):
    """Helper to see if updating a machine's location will move its plenary."""
    if old.hub != new.hub or old.building != new.building or \
       old.rack != new.rack:
        return True
    return False
