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
""" Contains the logic for `aq add interface --switch`."""


from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import Switch
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 assign_address)
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceSwitch(BrokerCommand):

    required_parameters = ["interface", "switch", "mac"]
    invalid_parameters = ['automac', 'ip', 'ipfromip', 'ipfromsystem',
                          'autoip', 'ipalgorithm', 'pg', 'autopg']

    def render(self, session, logger, interface, switch, mac, type, comments,
               **arguments):
        """This command can handle three cases:

        1) Switch is old-style, and has no IP address.  In that case,
        update_switch has to handle adding an IP, and this command can
        add the interface either now or later.

        2) Switch has an IP address with no interfaces.  Tie this interface
        in as providing the IP.  Not going to worry about propogating the
        extra information into DSDB.

        3) Switch has an IP address and an interface tied to that address.
        In this case, just record the new interface.

        """
        if type and type != "oa":
            raise ArgumentError("Only 'oa' is allowed as the interface type "
                                "for switches.")

        dbswitch = Switch.get_unique(session, switch, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbswitch)

        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise ArgumentError("Cannot use argument --%s when adding an "
                                    "interface to a switch" % arg)

        dbinterface = get_or_create_interface(session, dbswitch,
                                              name=interface, mac=mac,
                                              interface_type='oa',
                                              comments=comments, preclude=True)

        if dbswitch.primary_ip and not dbswitch.primary_name.assignments:
            assign_address(dbinterface, dbswitch.primary_ip,
                           dbswitch.primary_name.network)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        try:
            dsdb_runner.update_host(dbswitch, oldinfo)
        except AquilonError, err:
            raise ArgumentError("Could not update switch in DSDB: %s" % err)

        return
