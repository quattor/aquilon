# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""ConsoleServerHw formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.console_server_hw import ConsoleServerHw
from aquilon.aqdb.hw.hardware_entity import HardwareEntity


class ConsoleServerHwFormatter(ObjectFormatter):
    def format_raw(self, console_server_hw, indent=""):
        details = []
        for console_server in console_server_hw.console_server:
            details.append(self.redirect_raw(console_server, indent))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_raw(console_server_hw, indent))
        return "\n".join(details)

    def format_csv(self, console_server_hw):
        details = []
        for console_server in console_server_hw.console_server:
            details.append(self.redirect_csv(console_server))
        if not details:
            handler = ObjectFormatter.handlers[HardwareEntity]
            details.append(handler.format_csv(console_server_hw))
        return "\n".join(details)

ObjectFormatter.handlers[ConsoleServerHw] = ConsoleServerHwFormatter()


