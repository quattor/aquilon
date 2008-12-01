# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq unbind server --instance`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.unbind_server import CommandUnbindServer


class CommandUnbindServerInstance(CommandUnbindServer):

    required_parameters = ["hostname", "service", "instance"]

    def render(self, *args, **arguments):
        # The superclass already contains the logic to handle this case.
        return CommandUnbindServer.render(self, *args, **arguments)


