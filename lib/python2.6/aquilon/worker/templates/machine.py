# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.base import Plenary
from aquilon.worker import templates
from aquilon.worker.templates.panutils import pan, StructureTemplate, PanUnit

LOGGER = logging.getLogger(__name__)


class PlenaryMachineInfo(Plenary):
    def __init__(self, dbmachine, logger=LOGGER):
        Plenary.__init__(self, dbmachine, logger=logger)
        self.dbmachine = dbmachine
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
            self.room = loc.room.fullname
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
        self.plenary_core = (
                "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__)
        self.plenary_template = ("%(plenary_core)s/%(machine)s" % self.__dict__)
        self.dir = self.config.get("broker", "plenarydir")
        return

    def get_key(self):
        host = self.dbmachine.host
        cluster = self.dbmachine.cluster
        # Need a compile key if:
        # - There is a non-aurora host attached.
        # - This is a virtual machine in a cluster.
        if ((not host or self.dbmachine.model.machine_type == 'aurora_node')
                and (not cluster)):
            return None
        # We have at least host or cluster, maybe both...
        if host:
            # PlenaryHost is actually a PlenaryCollection... can't call
            # get_key() directly, so using get_remove_key().
            ph = templates.host.PlenaryHost(host, self.logger)
            host_key = ph.get_remove_key()
        if cluster:
            pc = templates.cluster.PlenaryClusterObject(cluster, self.logger)
            cluster_key = pc.get_key()
        if not cluster:
            return host_key
        if not host:
            return cluster_key
        # Just to make life fun, keep in mind that a virtual machine's guest
        # and the cluster may be in separate domains.
        return CompileKey.merge([host_key, cluster_key])

    def body(self, lines):
        ram = [StructureTemplate("hardware/ram/generic",
                                 {"size": PanUnit(self.dbmachine.memory, "MB")})]
        cpus = []
        for cpu_num in range(self.dbmachine.cpu_quantity):
            cpu = StructureTemplate("hardware/cpu/%s/%s" %
                                    (self.dbmachine.cpu.vendor.name,
                                     self.dbmachine.cpu.name))
            cpus.append(cpu)

        disks = {}
        for disk in self.dbmachine.disks:
            devname = disk.device_name
            if disk.disk_type == 'local':
                relpath = "hardware/harddisk/generic/%s" % disk.controller_type
                params = {"capacity": PanUnit(disk.capacity, "GB")}
                if disk.controller_type == 'cciss':
                    devname = "cciss/" + devname
            elif disk.disk_type == 'nas' and disk.service_instance:
                relpath = "service/nas_disk_share/%s/client/nasinfo" % \
                    disk.service_instance.name
                diskpath = "%s/%s.vmdk" % (self.machine, disk.device_name)
                params = {"capacity": PanUnit(disk.capacity, "GB"),
                          "interface": disk.controller_type,
                          "address": disk.address,
                          "path": diskpath}

            disks[devname] = StructureTemplate(relpath, params)

        managers = {}
        interfaces = {}
        for interface in self.dbmachine.interfaces:
            if interface.interface_type == 'public':
                ifinfo = {}
                if interface.mac:
                    ifinfo["hwaddr"] = interface.mac
                if interface.port_group:
                    ifinfo["port_group"] = interface.port_group
                if interface.bootable:
                    ifinfo["boot"] = interface.bootable
                interfaces[interface.name] = ifinfo
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
                    interfaces[interface.name] = {"hwaddr": interface.mac}

        # Firstly, location
        lines.append('"location" = %s;' % pan(self.sysloc))
        if self.rack:
            lines.append('"rack/name" = %s;' % pan(self.rack))
            if self.rackrow:
                lines.append('"rack/row" = %s;' % pan(self.rackrow))
            if self.rackcol:
                lines.append('"rack/column" = %s;' % pan(self.rackcol))
        if self.room:
            lines.append('"rack/room" = %s;' % pan(self.room))

        # And a chassis location?
        if self.dbmachine.chassis_slot:
            slot = self.dbmachine.chassis_slot[0]
            self.chassis = slot.chassis.fqdn
            self.slot = slot.slot_number
            lines.append('"chassis" = %s;' % pan(slot.chassis.fqdn))
            lines.append('"slot" = %d;' % slot.slot_number)

        #if self.hub:
        #    lines.append('"sysloc/hub" = "%s";' % self.hub)
        if self.campus:
            lines.append('"sysloc/campus" = %s;' % pan(self.campus))
        if self.dns_search_domains:
            lines.append('"sysloc/dns_search_domains" = %s;' %
                         pan(self.dns_search_domains))

        # Now describe the hardware
        lines.append("")
        if self.dbmachine.serial_no:
            lines.append('"serialnumber" = %s;' % pan(self.dbmachine.serial_no))
        lines.append('"nodename" = %s;' % pan(self.machine))
        lines.append("include { 'hardware/machine/%s/%s' };\n" %
                     (self.dbmachine.model.vendor.name,
                      self.dbmachine.model.name))

        lines.append("")
        lines.append('"ram" = %s;' % pan(ram))
        lines.append('"cpu" = %s;' % pan(cpus))
        if disks:
            lines.append('"harddisks" = %s;' % pan(disks))
        if interfaces:
            lines.append('"cards/nic" = %s;' % pan(interfaces))

        # /hardware/console needs "preferred" to be set, so we can't just use
        # pan() for the whole thing
        for manager in sorted(managers.keys()):
            params = managers[manager]
            lines.append('"console/%s" = %s;' % (manager, pan(params)))

    def write(self, *args, **kwargs):
        # Don't bother writing plenary files for dummy aurora hardware.
        if self.dbmachine.model.machine_type == 'aurora_node':
            return 0
        return Plenary.write(self, *args, **kwargs)


def machine_plenary_will_move(old, new):
    """Helper to see if updating a machine's location will move its plenary."""
    if old.hub != new.hub or old.building != new.building or \
       old.rack != new.rack:
        return True
    return False
