# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add hub`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.add_location import CommandAddLocation


class CommandAddHub(CommandAddLocation):

    required_parameters = ["name"]

    @add_transaction
    @az_check
    def render(self, session, name, fullname, comments, **arguments):
        return CommandAddLocation.render(self, session=session, name=name,
                type='hub', fullname=fullname,
                parentname='ms', parenttype='company',
                comments=comments, **arguments)


