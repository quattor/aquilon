# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq refresh network`."""


import logging
from threading import Lock

from twisted.python import log

from aquilon.server.broker import force_int, BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.aqdb.dsdb import DsdbConnection
from aquilon.aqdb.data_sync.net_refresh import NetRefresher


refresh_network_lock = Lock()


class CommandRefreshNetwork(BrokerCommand):

    required_parameters = ["building"]
    requires_format = True

    def render(self, session, user, building, dryrun, loglevel, **arguments):
        log.msg("Aquiring lock to refresh network for building %s" % building)
        refresh_network_lock.acquire()
        try:
            dbbuilding = get_location(session, building=building)

            # Doing this per-command makes no sense.  There should be a general
            # aqd-admin way of setting the per-component log level.
            verbosity = logging.WARN
            if loglevel:
                loglevel = force_int("loglevel", loglevel)
                if loglevel > 1:
                    verbosity = logging.DEBUG
                elif loglevel > 0:
                    verbosity = logging.INFO

            logger = logging.getLogger('net_refresh')
            logger.setLevel(verbosity)

            dsdb = DsdbConnection()
            try:
                nr = NetRefresher(dsdb, session, bldg=dbbuilding.name,
                                  commit=not(dryrun))
                nr.refresh()
            finally:
                dsdb.close()

            if dryrun:
                session.rollback()
        finally:
            log.msg("Released lock from refresh network for building %s" %
                    building)
            refresh_network_lock.release()

        return nr.report


