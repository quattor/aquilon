#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add country`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.add_location import CommandAddLocation


class CommandAddCountry(CommandAddLocation):

    required_parameters = ["name", "continent"]

    def render(self, session, name, continent, fullname, comments, **arguments):
        return CommandAddLocation.render(self, session=session, name=name,
                type='country', fullname=fullname,
                parentname=continent, parenttype='continent',
                comments=comments, **arguments)


#if __name__=='__main__':
