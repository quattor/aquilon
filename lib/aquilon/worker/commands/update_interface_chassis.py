# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq update interface --chassis`."""


from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.model import Chassis, Interface
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.interface import rename_interface
from aquilon.worker.processes import DSDBRunner


class CommandUpdateInterfaceChassis(BrokerCommand):

    required_parameters = ["interface", "chassis"]
    invalid_parameters = ['autopg', 'pg', 'boot', 'model', 'vendor']

    def render(self, session, logger, interface, chassis, mac, comments,
               rename_to, **arguments):
        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise UnimplementedError("update_interface --chassis cannot use "
                                         "the --%s option." % arg)

        dbchassis = Chassis.get_unique(session, chassis, compel=True)
        dbinterface = Interface.get_unique(session, hardware_entity=dbchassis,
                                           name=interface, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbchassis)

        if comments is not None:
            dbinterface.comments = comments
        if mac is not None:
            dbinterface.mac = mac
        if rename_to:
            rename_interface(session, dbinterface, rename_to)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbchassis, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update chassis in DSDB")

        return
