# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""ChassisHw formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.chassis_hw import ChassisHw
from aquilon.aqdb.hw.hardware_entity import HardwareEntity


class ChassisHwFormatter(ObjectFormatter):
    def format_raw(self, chassis_hw, indent=""):
        details = []
        for chassis in chassis_hw.chassis_hw:
            details.append(self.redirect_raw(chassis, indent))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_raw(chassis_hw, indent))
        return "\n".join(details)

    def format_csv(self, chassis_hw):
        details = []
        for chassis in chassis_hw.chassis_hw:
            details.append(self.redirect_csv(chassis))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_csv(chassis_hw))
        return "\n".join(details)

ObjectFormatter.handlers[ChassisHw] = ChassisHwFormatter()


