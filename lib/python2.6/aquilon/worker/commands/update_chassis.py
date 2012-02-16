# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Contains the logic for `aq update chassis`."""


from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.worker.broker import BrokerCommand
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
            update_primary_ip(session, dbchassis, ip)

        if comments is not None:
            dbchassis.comments = comments

        session.add(dbchassis)
        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        try:
            dsdb_runner.update_host(dbchassis, oldinfo)
        except AquilonError, err:
            raise ArgumentError("Could not update chassis in DSDB: %s" % err)
        return
