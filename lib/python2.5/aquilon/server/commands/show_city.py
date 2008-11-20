#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show city`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_location_type import CommandShowLocationType


class CommandShowCity(CommandShowLocationType):

    required_parameters = []

    def render(self, session, **arguments):
        return CommandShowLocationType.render(self, session=session,
                type='city', **arguments)


#if __name__=='__main__':
