# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

        if comments:
            dbinterface.comments = comments
        if mac:
            dbinterface.mac = mac
        if rename_to:
            rename_interface(session, dbinterface, rename_to)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbchassis, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update chassis in DSDB")

        return
