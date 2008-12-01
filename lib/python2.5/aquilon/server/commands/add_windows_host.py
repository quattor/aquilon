# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq add windows host`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.add_host import CommandAddHost


class CommandAddWindowsHost(CommandAddHost):

    required_parameters = ["hostname", "machine"]

    def render(self, *args, **kwargs):
        kwargs['archetype'] = 'windows'
        kwargs['domain'] = self.config.get("broker", "windows_host_domain")
        if 'buildstatus' not in kwargs:
            kwargs['buildstatus'] = 'build'
        # The superclass already contains the logic to handle this case.
        return CommandAddHost.render(self, *args, **kwargs)


