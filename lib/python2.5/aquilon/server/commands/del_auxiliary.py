#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del auxiliary`."""


import os

from twisted.python import log
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.processes import DSDBRunner
from aquilon.server.commands.del_host import delhost_lock
from aquilon.aqdb.sy.auxiliary import Auxiliary


class CommandDelAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    @add_transaction
    @az_check
    def render(self, session, auxiliary, user, **arguments):
        log.msg("Aquiring lock to attempt to delete %s" % auxiliary)
        delhost_lock.acquire()
        try:
            log.msg("Aquired lock, attempting to delete %s" % auxiliary)
            # Check dependencies, translate into user-friendly message
            dbauxiliary = get_system(session, auxiliary)
            if not isinstance(dbauxiliary, Auxiliary):
                raise ArgumentError("%s '%s' is not Auxiliary." % (
                                    dbauxiliary.system_type, dbauxiliary.fqdn))

            # FIXME: Look for System dependencies...

            ip = dbauxiliary.ip
            dbmachine = dbauxiliary.machine
            # FIXME: Check to see if this is handled auto-magically by
            # sqlalchemy.
            for dbinterface in dbauxiliary.interfaces:
                dbinterface.system = None
                session.update(dbinterface)

            session.delete(dbauxiliary)
            session.flush()
    
            try:
                dsdb_runner = DSDBRunner()
                dsdb_runner.delete_host_details(ip)
            except ProcessException, e:
                raise ArgumentError("Could not remove host %s from dsdb: %s" %
                            (auxiliary, e))
        finally:
            log.msg("Released lock from attempt to delete %s" % auxiliary)
            delhost_lock.release()

        if dbmachine.host:
            # FIXME: Reconfigure
            pass

        return


#if __name__=='__main__':
