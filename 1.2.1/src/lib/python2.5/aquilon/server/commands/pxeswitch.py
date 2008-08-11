#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq pxeswitch`."""


from socket import gethostbyname

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.exceptions_ import NameServiceError
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.processes import run_command


class CommandPxeswitch(BrokerCommand):

    required_parameters = ["hostname"]

    @add_transaction
    @az_check
    def render(self, session, hostname, boot, install, **arguments):
        # Right now configuration won't work if the host doesn't resolve.  If/when aii is fixed, this should
        # be change to a warning.  The check should only be made in prod though (which also means there's no unittest)
        if self.config.get("broker", "environment") == "prod":
            try:
                gethostbyname(hostname)
            except Exception, e:
                raise NameServiceError, e.args[1]

        dbhost = hostname_to_host(session, hostname)

        command = self.config.get("broker", "installfe")
        args = [command]
        if boot:
            args.append('--boot')
        elif install:
            args.append('--install')
        else:
            raise ArgumentError("Missing required boot or install parameter.")

        args.append(dbhost.fqdn)
        run_command(args)
        return


#if __name__=='__main__':
