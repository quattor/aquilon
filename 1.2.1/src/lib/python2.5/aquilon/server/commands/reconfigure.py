#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq reconfigure`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.make_aquilon import CommandMakeAquilon
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.exceptions_ import ArgumentError

class CommandReconfigure(CommandMakeAquilon):
    """The make aquilon command already contains the logic required."""

    required_parameters = ["hostname"]

    @az_check
    def render(self, session, hostname, user, **arguments):
        dbhost = hostname_to_host(session, hostname)

        buildlist = session.query(BuildItem).filter_by(host=dbhost).all()
        if (len(buildlist) == 0):
            raise ArgumentError("host %s has not been built. Run 'make_aquilon' first"%hostname)

        return CommandMakeAquilon.render(self, session=session, hostname=hostname, **arguments)


#if __name__=='__main__':
