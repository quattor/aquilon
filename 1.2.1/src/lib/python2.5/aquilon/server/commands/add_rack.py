#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add rack`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.add_location import CommandAddLocation


class CommandAddRack(CommandAddLocation):

    required_parameters = ["name", "building"]

    @add_transaction
    @az_check
    def render(self, session, name, building, fullname, comments, **arguments):
        return CommandAddLocation.render(self, session=session, name=name,
                type='rack', fullname=fullname,
                parentname=building, parenttype='building',
                comments=comments, **arguments)


#if __name__=='__main__':
