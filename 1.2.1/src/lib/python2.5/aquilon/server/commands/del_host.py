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


from threading import Lock

from twisted.python import log

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.processes import DSDBRunner


delhost_lock = Lock()


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    @add_transaction
    @az_check
    def render(self, session, hostname, user, **arguments):
        log.msg("Aquiring lock to attempt to delete %s" % hostname)
        delhost_lock.acquire()
        try:
            log.msg("Aquired lock, attempting to delete %s" % hostname)
            dbhost = hostname_to_host(session, hostname)
            session.refresh(dbhost)
            # Hack to make sure the machine object is refreshed in future queries.
            archetype = dbhost.archetype.name
            dbmachine = dbhost.machine
            session.refresh(dbmachine)
            ip = None
            for interface in dbmachine.interfaces:
                if interface.boot:
                    ip = interface.ip
            if not ip and archetype != 'aurora':
                raise ArgumentError("No boot interface found for host to delete from dsdb.")
    
            for template in dbhost.templates:
                log.msg("Before deleting host '%s', removing template '%s'"
                        % (dbhost.fqdn, template.cfg_path))
                session.delete(template)
            session.delete(dbhost)
            session.flush()
    
            if archetype != 'aurora':
                try:
                    dsdb_runner = DSDBRunner()
                    dsdb_runner.delete_host_details(ip)
                except ProcessException, e:
                    raise ArgumentError("Could not remove host %s from dsdb: %s" %
                            (hostname, e))

            # FIXME: Remove plenary template and profile.

            session.refresh(dbmachine)
        finally:
            log.msg("Released lock from attempt to delete %s" % hostname)
            delhost_lock.release()

        return


#if __name__=='__main__':
