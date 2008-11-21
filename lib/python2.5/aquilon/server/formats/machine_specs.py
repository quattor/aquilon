# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""MachineSpecs formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.machine_specs import MachineSpecs


class MachineSpecsFormatter(ObjectFormatter):
    def format_raw(self, machine_specs, indent=""):
        details = [indent + "MachineSpecs for %s %s:" %
                (machine_specs.model.vendor.name, machine_specs.model.name)]
        details.append(indent + "  Cpu: %s x %d" % (machine_specs.cpu.name,
            machine_specs.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine_specs.memory)
        details.append(indent + "  NIC count: %d" % machine_specs.nic_count)
        details.append(indent + "  Disk: sda %d GB %s" % 
               (machine_specs.disk_capacity, machine_specs.disk_type))
        if machine_specs.comments:
            details.append(indent + "  Comments: %s" % machine_specs.comments)
        return "\n".join(details)

ObjectFormatter.handlers[MachineSpecs] = MachineSpecsFormatter()


