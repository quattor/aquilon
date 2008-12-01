# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add continent`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.add_location import CommandAddLocation


class CommandAddContinent(CommandAddLocation):

    required_parameters = ["name", "hub"]

    def render(self, session, name, hub, fullname, comments, **arguments):
        return CommandAddLocation.render(self, session=session, name=name,
                type='continent', fullname=fullname,
                parentname=hub, parenttype='hub',
                comments=comments, **arguments)


