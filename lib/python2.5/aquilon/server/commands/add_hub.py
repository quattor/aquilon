# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add hub`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.add_location import CommandAddLocation


class CommandAddHub(CommandAddLocation):

    required_parameters = ["name"]

    def render(self, session, name, fullname, comments, **arguments):
        return CommandAddLocation.render(self, session=session, name=name,
                type='hub', fullname=fullname,
                parentname='ms', parenttype='company',
                comments=comments, **arguments)


