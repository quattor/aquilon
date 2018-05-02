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
"""Contains the logic for `aq bind console server`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ConsoleServer, ConsolePort, NetworkDevice
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.hardware_entity import get_hardware
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandBindConsoleServer(BrokerCommand):

    requires_plenaries = True
    required_parameters = ["console_server", "console_port"]

    def render(self, session, logger, plenaries, console_server, console_port,
               user, justification, reason,
               client_port, **kwargs):
        dbcons = ConsoleServer.get_unique(session, console_server, compel=True)
        dbhw_ent = get_hardware(session, **kwargs)

        # We expect most devices to have only a single client port...
        if not client_port:
            client_port = "console"

        if console_port in dbcons.ports:
            raise ArgumentError("Port {0!s} is already in use by {1:l}."
                                .format(console_port,
                                        dbcons.ports[console_port].client))
        for port in dbhw_ent.consoles:
            if port.client_port == client_port:
                raise ArgumentError("{0} already has console port '{1!s}' "
                                    "bound to {2:l}."
                                    .format(dbhw_ent, client_port,
                                            port.console_server))

        plenaries.add(dbhw_ent)

        dbcport = ConsolePort(console_server=dbcons, port_number=console_port,
                              client=dbhw_ent, client_port=client_port)
        dbcons.ports[console_port] = dbcport

        session.flush()

        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **kwargs)
        cm.consider(dbhw_ent)
        cm.validate()

        plenaries.write()

        return
