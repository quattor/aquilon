# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

import os
from tempfile import mkdtemp

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.data_sync.qip import QIPRefresh
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import run_command, remove_dir
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.locks import lock_queue, SyncKey


class CommandRefreshNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, building, dryrun, incremental,
               **arguments):
        if building:
            dbbuilding = get_location(session, building=building)
        else:
            dbbuilding = None

        # --dryrun and --incremental do not mix well
        if dryrun and incremental:
            raise ArgumentError("--dryrun and --incremental cannot be given "
                                "simultaneously.")

        key = SyncKey(data="network", logger=logger)
        lock_queue.acquire(key)

        rundir = self.config.get("broker", "rundir")
        tempdir = mkdtemp(prefix="refresh_network_", dir=rundir)
        try:
            args = [self.config.get("broker", "qip_dump_subnetdata"),
                    "--datarootdir", tempdir, "--format", "txt", "--noaudit"]
            run_command(args, logger=logger)

            subnetdata = file(os.path.join(tempdir, "subnetdata.txt"), "r")
            refresher = QIPRefresh(session, logger, dbbuilding, dryrun, incremental)
            refresher.refresh(subnetdata)

            session.flush()

            if dryrun:
                session.rollback()
        finally:
            lock_queue.release(key)
            remove_dir(tempdir, logger=logger)
