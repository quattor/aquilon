# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq update chassis`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.hardware_entity import update_primary_ip
from aquilon.worker.processes import DSDBRunner
from aquilon.aqdb.model import Model, Chassis


class CommandUpdateChassis(BrokerCommand):

    required_parameters = ["chassis"]

    def render(self, session, logger, chassis, model, rack, ip, vendor, serial,
               comments, **arguments):
        dbchassis = Chassis.get_unique(session, chassis, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbchassis)

        if vendor and not model:
            model = dbchassis.model.name
        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       machine_type='chassis', compel=True)
            dbchassis.model = dbmodel

        dblocation = get_location(session, rack=rack)
        if dblocation:
            dbchassis.location = dblocation

        if serial is not None:
            dbchassis.serial_no = serial

        if ip:
            update_primary_ip(session, logger, dbchassis, ip)

        if comments is not None:
            dbchassis.comments = comments

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbchassis, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update chassis in DSDB")

        return
