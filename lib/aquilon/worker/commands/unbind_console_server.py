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
"""Contains the logic for `aq unbind console server`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ConsoleServer, NetworkDevice
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.hardware_entity import get_hardware
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUnbindConsoleServer(BrokerCommand):

    requires_plenaries = True
    required_parameters = ["console_server"]

    def render(self, session, logger, plenaries, console_server, console_port,
               user, justification, reason,
               client_port=None, **kwargs):
        dbcons = ConsoleServer.get_unique(session, console_server, compel=True)

        found = set()

        if console_port:
            if console_port not in dbcons.ports:
                raise ArgumentError("Port {0!s} is not used."
                                    .format(console_port))
            found.add(dbcons.ports[console_port])
        else:
            dbhw_ent = get_hardware(session, **kwargs)
            for cport in dbhw_ent.consoles:
                if dbhw_ent.consoles[cport].console_server == dbcons and (client_port is None or
                                            dbhw_ent.consoles[cport].client_port == client_port):
                    found.add(dbhw_ent.consoles[cport])

            if not found:
                raise ArgumentError("{0} is not bound to {1:l}."
                                    .format(dbhw_ent, dbcons))


        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **kwargs)
        for port in found:
            cm.consider(port.client)
        cm.validate()

        for port in found:
            plenaries.add(port.client)
            del dbcons.ports[port.port_number]
            session.delete(port)

        session.flush()

        plenaries.write()

        return
