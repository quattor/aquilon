# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2015,2016,2017,2018  Contributor
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

from aquilon.aqdb.types import ChassisType
from aquilon.aqdb.model import Model, Chassis, HardwareEntity
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.hardware_entity import (
    get_default_chassis_grn_eonid,
    update_primary_ip,
)
from aquilon.worker.dbwrappers.location import get_location
from aquilon.exceptions_ import NotFoundException
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateChassis(BrokerCommand):

    required_parameters = ["chassis"]

    def render(self, session, logger, chassis, model, rack, ip, vendor, serial,
               comments, user, grn, eon_id, clear_grn, justification, reason,
               **arguments):
        dbchassis = Chassis.get_unique(session, chassis, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbchassis)

        if model:
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       model_type=ChassisType.Chassis)
            if not dbmodel:
                dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                           model_type=ChassisType.AuroraChassis)
            if not dbmodel:
                raise NotFoundException("Model {}, model type 'chassis' or 'aurora_chassis' not found.".format(model))
            dbchassis.model = dbmodel

        dblocation = get_location(session, rack=rack)
        if dblocation:
            dbchassis.location = dblocation

            # Validate ChangeManagement
            # Only if lacation being updated
            cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
            cm.consider(dbchassis)
            cm.validate()


        if serial is not None:
            dbchassis.serial_no = serial

        if ip:
            update_primary_ip(session, logger, dbchassis, ip)

        if comments is not None:
            dbchassis.comments = comments

        # If the request is to clear the GRN, reset it to the default one
        if clear_grn:
            grn, eon_id = get_default_chassis_grn_eonid(self.config)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            dbchassis.owner_grn = dbgrn

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbchassis, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update chassis in DSDB")

        return
