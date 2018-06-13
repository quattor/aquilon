# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Contains the logic for `aq del console server`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ConsoleServer
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.hardware_entity import check_only_primary_ip
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandDelConsoleServer(BrokerCommand):

    requires_plenaries = True
    required_parameters = ["console_server"]

    def render(self, session, logger, plenaries, console_server, clear_ports,
               user, justification, reason, **arguments):
        dbcons = ConsoleServer.get_unique(session, console_server, compel=True)

        check_only_primary_ip(dbcons)

        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbcons)
        cm.validate()

        if dbcons.ports:
            if not clear_ports:
                raise ArgumentError("{0} is still in use.  Specify "
                                    "--clear_ports if you really want to "
                                    "delete it.".format(dbcons))
            for port in dbcons.ports:
                plenaries.add(dbcons.ports[port].client)

        # Order matters here
        oldinfo = DSDBRunner.snapshot_hw(dbcons)
        dbdns_rec = dbcons.primary_name
        session.delete(dbcons)
        if dbdns_rec:
            delete_dns_record(dbdns_rec)

        session.flush()

        with plenaries.transaction():
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(None, oldinfo)
            dsdb_runner.commit_or_rollback("Could not remove console server from DSDB")

        return
