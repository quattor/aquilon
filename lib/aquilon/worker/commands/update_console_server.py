# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Contains the logic for `aq update console server`."""

from aquilon.aqdb.types import ConsoleServerType
from aquilon.aqdb.model import ConsoleServer, Model
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.hardware_entity import update_primary_ip
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateConsoleServer(BrokerCommand):

    required_parameters = ["console_server"]

    def render(self, session, logger, console_server, model, ip, vendor, serial,
               user, justification, reason, comments, **arguments):
        dbcons = ConsoleServer.get_unique(session, console_server, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbcons)

        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       model_type=ConsoleServerType.ConsoleServer,
                                       compel=True)
            dbcons.model = dbmodel

        dblocation = get_location(session, **arguments)
        if dblocation:
            dbcons.location = dblocation

        if serial is not None:
            dbcons.serial_no = serial

        if ip:
            update_primary_ip(session, logger, dbcons, ip)

        if comments is not None:
            dbcons.comments = comments

        session.flush()

        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbcons)
        cm.validate()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbcons, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update console server in DSDB")

        return
