# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq make aquilon`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.make import CommandMake

class CommandMakeAquilon(CommandMake):

    def render(self, **arguments):
        arguments['archetype'] = 'aquilon'
        return CommandMake.render(self, **arguments)


