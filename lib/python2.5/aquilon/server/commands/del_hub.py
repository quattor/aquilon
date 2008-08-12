#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del hub`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.del_location import CommandDelLocation


class CommandDelHub(CommandDelLocation):

    required_parameters = ["name"]

    @add_transaction
    @az_check
    def render(self, session, name, **arguments):
        return CommandDelLocation.render(self, session=session, name=name,
                type='hub', **arguments)


#if __name__=='__main__':
