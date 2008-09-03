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

from aquilon.server.templates.base import Plenary

class PlenaryMachineInfo(Plenary):
    def __init__(self, dbmachine):
        Plenary.__init__(self)
        self.hub = dbmachine.location.hub.fullname.lower()
        self.building = dbmachine.location.building.name
        if dbmachine.location.rack:
            self.rack = dbmachine.location.rack.name
        else:
            self.rack = None
        self.sysloc = dbmachine.location.sysloc()
        self.machine = dbmachine.name
        self.model = dbmachine.model.name
        self.machine_type = dbmachine.model.machine_type
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
            self.interfaces.append({"name":interface.name,
                                    "mac":interface.mac,
                                    "boot":interface.bootable})
        self.model_relpath = (
            "hardware/machine/%(vendor)s/%(model)s" % self.__dict__)
        self.plenary_core = (
                "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__)
        self.plenary_template = ("%(plenary_core)s/%(machine)s" % self.__dict__)
        return

    def body(self, lines):
        lines.append('"location" = "%(sysloc)s";' % self.__dict__)
        if self.serial:
            lines.append('"serialnumber" = "%(serial)s";\n' % self.__dict__)
        lines.append('"nodename" = "%(machine)s";' % self.__dict__)
        lines.append("")
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

