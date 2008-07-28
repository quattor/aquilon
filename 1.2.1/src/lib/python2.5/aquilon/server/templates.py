#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Any work by the broker to write out (or read in?) templates lives here."""

import os
from datetime import datetime

from aquilon.aqdb.net.ipcalc import Network
from aquilon.server.processes import write_file, read_file, remove_file


class PlenaryMachineInfo(object):
    def __init__(self, dbmachine):
        self.hub = dbmachine.location.hub.fullname.lower()
        self.building = dbmachine.location.building.name
        self.rack = dbmachine.location.rack.name
        self.sysloc = dbmachine.location.sysloc()
        self.machine = dbmachine.name
        self.model = dbmachine.model.name
        self.vendor = dbmachine.model.vendor.name
        self.serial = dbmachine.serial_no
        self.ram = dbmachine.memory
        self.num_cpus = dbmachine.cpu_quantity
        self.cpu_relpath = "hardware/cpu/%s/%s" % (
                dbmachine.cpu.vendor.name, dbmachine.cpu.name)
        harddisks = []
        for harddisk in dbmachine.disks:
            relpath = "hardware/harddisk/generic/%s" % harddisk.disk_type.type
            harddisks.append({"relpath":relpath, "capacity":harddisk.capacity,
                "name":harddisk.device_name})
        self.harddisks = harddisks
        self.interfaces = []
        for interface in dbmachine.interfaces:
            self.interfaces.append(
                    {"name":interface.name, "mac":interface.mac,
                        "boot":interface.boot})
        self.model_relpath = (
            "hardware/machine/%(vendor)s/%(model)s" % self.__dict__)
        self.plenary_core = (
                "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__)
        self.plenary_struct = ("%(plenary_core)s/%(machine)s" % self.__dict__)
        self.plenary_template = ("%(plenary_struct)s.tpl" % self.__dict__)
        return

    def write(self, plenarydir, localhost, user):
        lines = []
        lines.append("# Generated on %s for %s at %s UTC"
                % (localhost, user, datetime.utcnow().ctime()))
        lines.append("structure template %(plenary_struct)s;\n" % self.__dict__)
        lines.append('"location" = "%(sysloc)s";' % self.__dict__)
        if self.serial:
            lines.append('"serialnumber" = "%(serial)s";\n' % self.__dict__)
        lines.append("include { '%(model_relpath)s' };\n" % self.__dict__)
        lines.append('"ram" = list(create("hardware/ram/generic", "size", %(ram)d*MB));'
                % self.__dict__)
        lines.append('"cpu" = list(' + ", \n             ".join(
                ['create("%(cpu_relpath)s")' % self.__dict__
                for cpu_num in range(self.num_cpus)]) + ');')
        if self.harddisks:
            lines.append('"harddisks" = nlist(' + 
                    ", ".join(['"%(name)s", create("%(relpath)s", "capacity", %(capacity)d*GB)' %
                    hd for hd in self.harddisks]) +
                    ');\n')
        for interface in self.interfaces:
            lines.append('"cards/nic/%s/hwaddr" = "%s";'
                    % (interface['name'], interface['mac'].upper()))
            if interface['boot']:
                lines.append('"cards/nic/%s/boot" = %s;'
                        % (interface['name'], str(interface['boot']).lower()))
        lines.append("")

        plenary_path = os.path.join(plenarydir, self.plenary_core)
        plenary_file = os.path.join(plenarydir, self.plenary_template)
        if not os.path.exists(plenary_path):
            os.makedirs(plenary_path)
        write_file(plenary_file, "\n".join(lines))
        return

    def read(self, plenarydir):
        return read_file(plenarydir, self.plenary_template)

    def remove(self, plenarydir):
        plenary_file = os.path.join(plenarydir, self.plenary_template)
        remove_file(plenary_file)
        return

    def reconfigure(self, dbhost, tempdir, localhost, user):
        fqdn = dbhost.fqdn

        # FIXME: Need at least one interface marked boot - that one first
        # FIXME: Method for obtaining broadcast / gateway, netmask hard-coded.
        # The IPAddress table has not yet been defined in interface.py.
        interfaces = []
        for dbinterface in dbhost.machine.interfaces:
            if not dbinterface.ip or dbinterface.ip == '0.0.0.0':
                continue
            net = Network(dbinterface.ip, 25)
            # Fudge the gateway as the network + 1
            gateway_components = net.network().dq.split('.')
            gateway_components[-1] = str(int(gateway_components[-1]) + 1)
            gateway = ".".join(gateway_components)
            interfaces.append({"ip":net.dq,
                    "netmask":net.netmask().dq,
                    "broadcast":net.broadcast().dq,
                    "gateway":gateway,
                    "bootproto":"dhcp",
                    "name":dbinterface.name})

        os_template = None
        personality_template = None
        services = []
        for t in dbhost.templates:
            if t.cfg_path.tld.type == 'os':
                os_template = repr(t.cfg_path) + '/config'
            elif t.cfg_path.tld.type == 'personality':
                personality_template = repr(t.cfg_path) + '/config'
            elif t.cfg_path.tld.type == 'service':
                services.append(repr(t.cfg_path) + '/client/config')
            # FIXME: Features should also be here...

        templates = []
        templates.append("archetype/base")
        templates.append(os_template)
        for service in services:
            templates.append(service)
        templates.append(personality_template)
        templates.append("archetype/final")

        lines = []
        lines.append("#Generated on %s for %s at %s UTC"
                % (localhost, user, datetime.utcnow().ctime()))
        lines.append("object template %s;\n" % fqdn)
        lines.append("include { 'pan/units' };\n")
        lines.append("'/hardware' = create('%(plenary_struct)s');\n" % self.__dict__)
        for interface in interfaces:
            lines.append("'/system/network/interfaces/%(name)s' = nlist('ip', '%(ip)s', 'netmask', '%(netmask)s', 'broadcast', '%(broadcast)s', 'gateway', '%(gateway)s', 'bootproto', '%(bootproto)s');" % interface)
        lines.append("\n")
        for template in templates:
            lines.append("include { '%s' };" % template)
        lines.append("")

        template_file = os.path.join(tempdir, fqdn + '.tpl')
        write_file(template_file, "\n".join(lines))
        return


#if __name__=='__main__':
