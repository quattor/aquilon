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
""" Contains the logic for `aq add interface --chassis`.
    Duplicates logic used in `aq add interface --tor_switch`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import Chassis
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.interface import get_or_create_interface
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceChassis(BrokerCommand):

    required_parameters = ["interface", "chassis", "mac"]
    invalid_parameters = ["automac", "pg", "autopg", "model", "vendor"]

    def render(self, session, logger, interface, chassis, mac, type, comments,
               **arguments):
        if type and type != "oa":
            raise ArgumentError("Only 'oa' is allowed as the interface type "
                                "for chassis.")

        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise ArgumentError("Cannot use argument --%s when adding an "
                                    "interface to a chassis." % arg)

        dbchassis = Chassis.get_unique(session, chassis, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbchassis)

        dbinterface = get_or_create_interface(session, dbchassis,
                                              name=interface, mac=mac,
                                              interface_type='oa',
                                              comments=comments, preclude=True)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        try:
            dsdb_runner.update_host(dbchassis, oldinfo)
        except ProcessException, err:
            raise ArgumentError("Could not update chassis in DSDB: %s" % err)

        return
