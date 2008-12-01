# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del building`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.del_location import CommandDelLocation


class CommandDelBuilding(CommandDelLocation):

    required_parameters = ["name"]

    def render(self, session, name, **arguments):
        return CommandDelLocation.render(self, session=session, name=name,
                type='building', **arguments)


