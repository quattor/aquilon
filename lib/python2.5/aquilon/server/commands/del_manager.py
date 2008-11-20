#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del manager`."""


import os

from twisted.python import log
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.processes import DSDBRunner
from aquilon.server.commands.del_host import delhost_lock
from aquilon.aqdb.sy.manager import Manager


class CommandDelManager(BrokerCommand):

    required_parameters = ["manager"]

    def render(self, session, manager, user, **arguments):
        log.msg("Aquiring lock to attempt to delete %s" % manager)
        delhost_lock.acquire()
        try:
            log.msg("Aquired lock, attempting to delete %s" % manager)
            # Check dependencies, translate into user-friendly message
            dbmanager = get_system(session, manager, Manager, 'Manager')

            # FIXME: Look for System dependencies...

            ip = dbmanager.ip
            dbmachine = dbmanager.machine
            # FIXME: Check to see if this is handled auto-magically by
            # sqlalchemy.
            for dbinterface in dbmanager.interfaces:
                dbinterface.system = None
                session.update(dbinterface)

            session.delete(dbmanager)
            session.flush()
    
            try:
                dsdb_runner = DSDBRunner()
                dsdb_runner.delete_host_details(ip)
            except ProcessException, e:
                raise ArgumentError("Could not remove host %s from dsdb: %s" %
                            (manager, e))
        finally:
            log.msg("Released lock from attempt to delete %s" % manager)
            delhost_lock.release()

        if dbmachine.host:
            # FIXME: Reconfigure
            pass

        return


#if __name__=='__main__':
