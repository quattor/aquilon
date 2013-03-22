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
""" Contains the logic for `aq add interface --switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Switch
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.interface import get_or_create_interface
from aquilon.worker.processes import DSDBRunner


class CommandAddInterfaceSwitch(BrokerCommand):

    required_parameters = ["interface", "switch"]
    invalid_parameters = ["automac", "pg", "autopg", "model", "vendor"]
    valid_interface_types = ["oa", "loopback"]

    def render(self, session, logger, interface, switch, mac, type, comments,
               **arguments):
        if type and type not in self.valid_interface_types:
            raise ArgumentError("Interface type %s is not allowed for "
                                "switches." % type)

        if not type:
            if interface.lower().startswith("lo"):
                type = "loopback"
            else:
                type = "oa"

        for arg in self.invalid_parameters:
            if arguments.get(arg) is not None:
                raise ArgumentError("Cannot use argument --%s when adding an "
                                    "interface to a switch." % arg)

        dbswitch = Switch.get_unique(session, switch, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbswitch)

        dbinterface = get_or_create_interface(session, dbswitch,
                                              name=interface, mac=mac,
                                              interface_type=type,
                                              comments=comments, preclude=True)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.update_host(dbswitch, oldinfo)
        dsdb_runner.commit_or_rollback("Could not update switch in DSDB")

        return
