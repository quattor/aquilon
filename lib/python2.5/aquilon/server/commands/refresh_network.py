# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq refresh network`."""


from threading import Lock

from aquilon.exceptions_ import PartialError
from aquilon.server.broker import BrokerCommand
from aquilon.server.logger import CLIENT_INFO
from aquilon.server.dbwrappers.location import get_location
from aquilon.aqdb.dsdb import DsdbConnection
from aquilon.aqdb.data_sync.net_refresh import NetRefresher


refresh_network_lock = Lock()


class CommandRefreshNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, building, dryrun, incremental,
               **arguments):
        if building:
            action = "refresh network for building %s" % building
        else:
            action = "refresh all networks"
        logger.client_info("Acquiring lock to %s", action)
        refresh_network_lock.acquire()
        logger.client_info("Lock acquired.")
        try:
            if building:
                dbbuilding = get_location(session, building=building)
                building = dbbuilding.name

            dsdb = DsdbConnection()
            try:
                nr = NetRefresher(dsdb, session, bldg=building,
                                  logger=logger, loglevel=CLIENT_INFO,
                                  incremental=incremental, dryrun=dryrun)
                nr.refresh()
            finally:
                dsdb.close()

            if nr.errors:
                if incremental:
                    msg = ''
                else:
                    msg = 'No changes applied because of errors.'
                raise PartialError(success=[], failed=nr.errors,
                                   success_msg=msg)
            if dryrun:
                session.rollback()
        finally:
            logger.client_info("Released lock from %s", action)
            refresh_network_lock.release()

        return
