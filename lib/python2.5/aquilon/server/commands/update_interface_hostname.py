# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update interface --hostname`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.update_interface_machine import (
        CommandUpdateInterfaceMachine)
from aquilon.server.dbwrappers.host import hostname_to_host


class CommandUpdateInterfaceHostname(CommandUpdateInterfaceMachine):

    required_parameters = ["hostname", "interface"]

    def render(self, session, hostname, **arguments):
        dbhost = hostname_to_host(session, hostname)
        arguments['machine'] = dbhost.machine.name
        return CommandUpdateInterfaceMachine.render(self, session=session,
                                                    hostname=hostname,
                                                    **arguments)


