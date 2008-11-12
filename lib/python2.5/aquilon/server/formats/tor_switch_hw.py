#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""TorSwitchHw formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.tor_switch_hw import TorSwitchHw
from aquilon.aqdb.hw.hardware_entity import HardwareEntity


class TorSwitchHwFormatter(ObjectFormatter):
    def format_raw(self, tor_switch_hw, indent=""):
        details = []
        for tor_switch in tor_switch_hw.tor_switch:
            details.append(self.redirect_raw(tor_switch, indent))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_raw(tor_switch_hw, indent))
        return "\n".join(details)

    def format_csv(self, tor_switch_hw):
        details = []
        for tor_switch in tor_switch_hw.tor_switch:
            details.append(self.redirect_csv(tor_switch))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_csv(tor_switch_hw))
        return "\n".join(details)

ObjectFormatter.handlers[TorSwitchHw] = TorSwitchHwFormatter()


#if __name__=='__main__':
