# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Any work by the broker to write out (or read in?) templates lives here."""


import logging

from aquilon.aqdb.model import Machine
from aquilon.worker.locks import CompileKey
from aquilon.aqdb.data_sync.storage import find_storage_data
from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include, PanMetric,
                                               PanEscape)

LOGGER = logging.getLogger(__name__)


class PlenaryMachineInfo(Plenary):

    template_type = "structure"

    def __init__(self, dbmachine, logger=LOGGER):
        Plenary.__init__(self, dbmachine, logger=logger)
        self.machine = dbmachine.label

        loc = dbmachine.location
        self.hub = loc.hub.fullname.lower()
        self.building = loc.building.name
        if loc.rack:
            self.rack = loc.rack.name
            self.rackrow = loc.rack.rack_row
            self.rackcol = loc.rack.rack_column
        else:
            self.rack = None
        if loc.room:
            self.room = loc.room.name
        else:
            self.room = None

        self.dns_search_domains = []
        parents = loc.parents[:]
        parents.append(loc)
        parents.reverse()
        for parent in parents:
            # Filter out duplicates
            extra_domains = [map.dns_domain.name
                             for map in parent.dns_maps
                             if map.dns_domain.name not in self.dns_search_domains]
            self.dns_search_domains.extend(extra_domains)

        if loc.campus:
            self.campus = loc.campus.name
        else:
            self.campus = None

        self.sysloc = loc.sysloc()

        # If this changes need to update machine_plenary_will_move() to match.
        self.plenary_core = "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__
        self.plenary_template = self.machine

    def get_key(self):
        host = self.dbobj.host
        container = self.dbobj.vm_container
        # Need a compile key if:
        # - There is a host attached.
        # - This is a virtual machine in a container.
        if not host and not container:
            return None
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

            if disk.disk_type == 'local':
                tpl = StructureTemplate(
                                        ("hardware/harddisk/generic/%s" %
                                        disk.controller_type),
                                        params)

                if disk.controller_type == 'cciss':
                    devname = "cciss/" + devname
            elif disk.disk_type == 'virtual_disk':
                share = disk.share
                share_info = find_storage_data(share)

                params["path"] = "%s/%s.vmdk" % (self.machine, disk.device_name)
                params["address"] = disk.address
                params["sharename"] = share.name
                params["server"] = share_info["server"]
                params["mountpoint"] = share_info["mount"]

                tpl = params

            disks[PanEscape(devname)] = tpl

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
        pan_assign(lines, "location", self.sysloc)
        if self.rack:
            pan_assign(lines, "rack/name", self.rack)
            if self.rackrow:
                pan_assign(lines, "rack/row", self.rackrow)
            if self.rackcol:
                pan_assign(lines, "rack/column", self.rackcol)
        if self.room:
            pan_assign(lines, "rack/room", self.room)

        # And a chassis location?
        if self.dbobj.chassis_slot:
            slot = self.dbobj.chassis_slot[0]
            pan_assign(lines, "chassis", slot.chassis.fqdn)
            pan_assign(lines, "slot", slot.slot_number)

        #if self.hub:
        #    pan_assign(lines, "sysloc/hub", self.hub)
        if self.campus:
            pan_assign(lines, "sysloc/campus", self.campus)
        if self.dns_search_domains:
            pan_assign(lines, "sysloc/dns_search_domains",
                       self.dns_search_domains)

        # Now describe the hardware
        lines.append("")
        if self.dbobj.serial_no:
            pan_assign(lines, "serialnumber", self.dbobj.serial_no)
        pan_assign(lines, "nodename", self.machine)
        pan_include(lines, "hardware/machine/%s/%s" %
                    (self.dbobj.model.vendor.name, self.dbobj.model.name))

        lines.append("")
        pan_assign(lines, "ram", ram)
        pan_assign(lines, "cpu", cpus)
        if disks:
            pan_assign(lines, "harddisks", disks)
        if interfaces:
            pan_assign(lines, "cards/nic", interfaces)

        # /hardware/console/preferred must be set, so we can't assign to
        # "/console" directly
        for manager in sorted(managers.keys()):
            pan_assign(lines, "console/%s" % manager, managers[manager])

    def write(self, *args, **kwargs):
        return Plenary.write(self, *args, **kwargs)


Plenary.handlers[Machine] = PlenaryMachineInfo


def machine_plenary_will_move(old, new):
    """Helper to see if updating a machine's location will move its plenary."""
    if old.hub != new.hub or old.building != new.building or \
       old.rack != new.rack:
        return True
    return False
