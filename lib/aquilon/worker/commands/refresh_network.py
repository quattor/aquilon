# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq refresh network`."""

import os
from tempfile import mkdtemp

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.data_sync.qip import QIPRefresh
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import run_command
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.locks import SyncKey
from aquilon.utils import remove_dir


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

        with SyncKey("network", logger=logger):
            rundir = self.config.get("broker", "rundir")
            tempdir = mkdtemp(prefix="refresh_network_", dir=rundir)
            try:
                args = [self.config.get("broker", "qip_dump_subnetdata"),
                        "--datarootdir", tempdir, "--format", "txt",
                        "--noaudit"]
                run_command(args, logger=logger)

                refresher = QIPRefresh(session, logger, dbbuilding, dryrun,
                                       incremental)

                with open(os.path.join(tempdir, "subnetdata.txt"), "r") as f:
                    refresher.refresh(f)

                session.flush()

                if dryrun:
                    session.rollback()
            finally:
                remove_dir(tempdir, logger=logger)
