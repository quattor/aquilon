# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Chassis formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Chassis


class ChassisFormatter(ObjectFormatter):
    def format_raw(self, chassis, indent=""):
        details = [indent + "%s: %s" %
                (chassis.chassis_hw.model.machine_type.capitalize(),
                 chassis.fqdn)]
        if chassis.ip:
            details.append(indent + "  IP: %s" % chassis.ip)
        details.append(self.redirect_raw(chassis.chassis_hw.location,
                                         indent+"  "))
        details.append(self.redirect_raw(chassis.chassis_hw.model,
                                         indent + "  "))
        if chassis.chassis_hw.serial_no:
            details.append(indent + "  Serial: %s" %
                           chassis.chassis_hw.serial_no)
        for slot in chassis.slots:
            if slot.machine:
                details.append(indent + "  Slot #%d: %s" %
			       (slot.slot_number, slot.machine.name))
            else:
                details.append(indent + "  Slot #%d Unknown" %
                               slot.slot_number)
        for i in chassis.chassis_hw.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if chassis.comments:
            details.append(indent + "  Comments: %s" % chassis.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Chassis] = ChassisFormatter()


