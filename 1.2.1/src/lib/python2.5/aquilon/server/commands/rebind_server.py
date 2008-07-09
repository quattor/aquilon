#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq rebind server`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.bind_server import CommandBindServer


class CommandRebindServer(CommandBindServer):

    required_parameters = ["hostname", "service", "instance"]

    @add_transaction
    @az_check
    def render(self, *args, **arguments):
        arguments["force"] = True
        return CommandBindServer.render(self, *args, **arguments)


#if __name__=='__main__':
