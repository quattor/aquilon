# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Any work by the broker to write out (or read in?) templates lives here."""


from aquilon.server.templates.base import Plenary


class PlenaryMachineInfo(Plenary):
    def __init__(self, dbmachine):
        Plenary.__init__(self)
        loc = dbmachine.location
        self.hub = loc.hub.fullname.lower()
        self.building = loc.building.name
        if loc.rack:
            self.rack = loc.rack.name
            self.rackrow = loc.rack.rack_row
            self.rackcol = loc.rack.rack_column
        else:
            self.rack = None
        #if loc.campus:
        #    self.campus = loc.campus.fullname.lower().strip().replace(" ", "-")
        #else:
        #    self.campus = None
        #if loc.hub:
        #   self.hub = loc.hub.fullname.lower()
        #else:
        #   self.hub = None
        
        # And a chassis location?
        if dbmachine.chassis_slot:
            slot = dbmachine.chassis_slot[0]
            self.chassis = slot.chassis.fqdn
            self.slot = slot.slot_number
        else:
            self.chassis = None

        self.sysloc = loc.sysloc()
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
        self.managers = []
        self.interfaces = []
        for interface in dbmachine.interfaces:
            if interface.interface_type == 'public':
                self.interfaces.append({"name":interface.name,
                                        "mac":interface.mac,
                                        "boot":interface.bootable})
                continue
            if interface.interface_type == 'management':
                manager = {"type":interface.name, "mac":interface.mac,
                           "ip":None, "fqdn":None}
                if interface.system:
                    manager["ip"] = interface.system.ip
                    manager["fqdn"] = interface.system.fqdn
                self.managers.append(manager)
                continue
        self.model_relpath = (
            "hardware/machine/%(vendor)s/%(model)s" % self.__dict__)
        self.plenary_core = (
                "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__)
        self.plenary_template = ("%(plenary_core)s/%(machine)s" % self.__dict__)
        self.dir = self.config.get("broker", "plenarydir")
        return

    def body(self, lines):
        # Firstly, location
        lines.append('"location" = "%(sysloc)s";' % self.__dict__)
        if self.rack:
            lines.append('"rack/name" = "%(rack)s";' % self.__dict__)
            if self.rackrow:
                lines.append('"rack/row" = "%(rackrow)s";' % self.__dict__)
            if self.rackcol:
                lines.append('"rack/column" = "%(rackcol)s";' % self.__dict__)

        # And a chassis location?
        if self.chassis:
            lines.append('"chassis" = "%s";'%self.chassis)
            lines.append('"slot" = %d;'%self.slot)

        #if self.hub:
        #    lines.append('"sysloc/hub" = "%s";' % self.hub)
        #if self.campus:
        #    lines.append('"sysloc/campus" = "%s";' % self.campus)

        # Now describe the hardware
        lines.append("")
        if self.serial:
            lines.append('"serialnumber" = "%(serial)s";\n' % self.__dict__)
        lines.append('"nodename" = "%(machine)s";' % self.__dict__)
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
        for manager in self.managers:
            lines.append('"console/%(type)s" = nlist(' % manager)
            lines.append('                           "hwaddr", "%(mac)s"' %
                         manager)
            if (manager["fqdn"]):
                lines.append('                           , "fqdn", "%(fqdn)s"' %
                             manager)
            lines.append('                     );')


