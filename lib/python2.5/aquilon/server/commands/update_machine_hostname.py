# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update machine --hostname`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.update_machine import CommandUpdateMachine
from aquilon.server.dbwrappers.host import hostname_to_host


class CommandUpdateMachineHostname(CommandUpdateMachine):

    required_parameters = ["hostname"]

    def render(self, session, hostname, **arguments):
        dbhost = hostname_to_host(session, hostname)
        arguments['machine'] = dbhost.machine.name
        return CommandUpdateMachine.render(self, session=session, **arguments)


