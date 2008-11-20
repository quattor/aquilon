#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add interface --hostname`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.add_interface_machine import (
        CommandAddInterfaceMachine)
from aquilon.server.dbwrappers.host import hostname_to_host


class CommandAddInterfaceHostname(CommandAddInterfaceMachine):

    required_parameters = ["hostname", "mac", "interface"]

    def render(self, session, hostname, **arguments):
        dbhost = hostname_to_host(session, hostname)
        arguments['machine'] = dbhost.machine.name
        return CommandAddInterfaceMachine.render(self, session=session,
                                                 **arguments)


#if __name__=='__main__':
