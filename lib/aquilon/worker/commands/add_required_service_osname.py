# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError, AuthorizationException
from aquilon.aqdb.model import (Archetype, Personality, PersonalityStage,
                                OperatingSystem, Service, Host)
from aquilon.aqdb.model.host_environment import Production
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.commands.deploy import validate_justification


class CommandAddRequiredServiceOsname(BrokerCommand):

    required_parameters = ["service", "archetype", "osname", "osversion"]

    def _update_dbobj(self, dbos, dbservice):
        if dbservice in dbos.required_services:
            raise ArgumentError("{0} is already required by {1:l}."
                                .format(dbservice, dbos))
        dbos.required_services.append(dbservice)

    def render(self, session, service, archetype, osname, osversion,
               justification, reason, user, **arguments):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=dbarchetype, compel=True)
        dbservice = Service.get_unique(session, service, compel=True)
        prod = Production.get_instance(session)

        q = session.query(Host.hardware_entity_id)
        q = q.filter_by(operating_system=dbos)
        q = q.join(PersonalityStage, Personality)
        q = q.filter_by(host_environment=prod)
        if q.count():
            if not justification:
                raise AuthorizationException("Changing the required services of "
                                             "an operating system requires "
                                             "--justification.")
            validate_justification(user, justification, reason)

        self._update_dbobj(dbos, dbservice)
        session.flush()
        return
