#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Machine formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.systems import Machine


class MachineFormatter(ObjectFormatter):
    def format_raw(self, machine, indent=""):
        details = [indent + "%s: %s" %
                (machine.type().capitalize(), machine.name)]
        if machine.host:
            details.append(indent + "  Allocated to host: %s"
                    % machine.host.fqdn)
        details.append(self.redirect_raw(machine.location, indent + "  "))
        details.append(self.redirect_raw(machine.model, indent + "  "))
        details.append(indent + "  Cpu: %s x %d" %
                (machine.cpu, machine.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine.memory)
        if machine.serial_no:
            details.append(indent + "  Serial: %s" % machine.serial_no)
        for d in machine.disks:
            details.append(indent + "  Disk: %d GB %s"
                    % (d.capacity, d.type.type))
        for i in machine.interfaces:
            details.append(indent + "  Interface: %s %s %s boot=%s" 
                    % (i.name, i.mac, i.ip, i.boot))
        for p in machine.switchport:
            if p.interface:
                details.append(indent + "  Switch Port %d: %s %s %s" %
                        (p.port_number, p.interface.machine.type(),
                            p.interface.machine.name, p.interface.name))
            else:
                details.append(indent +
                        "  Switch Port %d: No interface recorded in aqdb" %
                        p.port_number)
        if machine.comments:
            details.append(indent + "  Comments: %s" % machine.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Machine] = MachineFormatter()


#if __name__=='__main__':
