#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del host`."""


from twisted.python import log

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.processes import DSDBRunner


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    @add_transaction
    @az_check
    def render(self, session, hostname, user, **arguments):
        dbhost = hostname_to_host(session, hostname)
        session.refresh(dbhost)
        # Hack to make sure the machine object is refreshed in future queries.
        dbmachine = dbhost.machine
        session.refresh(dbmachine)
        ip = None
        for interface in dbmachine.interfaces:
            if interface.boot:
                ip = interface.ip
        if not ip:
            raise ArgumentError("No boot interface found for host to delete from dsdb.")

        for template in dbhost.templates:
            log.msg("Before deleting host '%s', removing template '%s'"
                    % (dbhost.fqdn, template.cfg_path))
            session.delete(template)
        session.delete(dbhost)
        session.flush()

        dsdb_runner = DSDBRunner()
        dsdb_runner.delete_host_details(ip)

        # FIXME: Remove plenary template and profile.

        session.refresh(dbmachine)
        return


#if __name__=='__main__':
