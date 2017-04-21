# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq add required service --osname`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Archetype, OperatingSystem, Service
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddRequiredServiceOsname(BrokerCommand):

    required_parameters = ["service", "archetype", "osname", "osversion"]

    def _update_dbobj(self, dbos, dbservice):
        if dbservice in dbos.required_services:
            raise ArgumentError("{0} is already required by {1:l}."
                                .format(dbservice, dbos))
        dbos.required_services.append(dbservice)

    def render(self, session, logger, service, archetype, osname, osversion,
               justification, reason, user, **_):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        dbarchetype.require_compileable("required services are not supported")

        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=dbarchetype, compel=True)
        dbservice = Service.get_unique(session, service, compel=True)

        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.validate(dbos)

        self._update_dbobj(dbos, dbservice)
        session.flush()
        return
