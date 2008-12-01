# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show country --name`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.show_location_type import CommandShowLocationType


class CommandShowCountryName(CommandShowLocationType):

    required_parameters = ["name"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, name, **arguments):
        return CommandShowLocationType.render(self, session=session, name=name,
                type='country', **arguments)


