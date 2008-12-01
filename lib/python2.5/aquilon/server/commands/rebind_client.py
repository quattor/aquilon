# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq rebind client`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.bind_client import CommandBindClient


class CommandRebindClient(CommandBindClient):

    required_parameters = ["hostname", "service"]

    @add_transaction
    @az_check
    def render(self, *args, **arguments):
        arguments["force"] = True
        return CommandBindClient.render(self, *args, **arguments)


