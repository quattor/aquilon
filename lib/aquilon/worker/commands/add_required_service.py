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
"""Contains the logic for `aq add required service`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Archetype, Service
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_archetype


class CommandAddRequiredService(BrokerCommand):

    required_parameters = ["service", "archetype"]

    def _update_dbobj(self, dbarchetype, dbservice):
        if dbservice in dbarchetype.required_services:
            raise ArgumentError("{0} is already required by {1:l}."
                                .format(dbservice, dbarchetype))
        dbarchetype.required_services.append(dbservice)

    def render(self, session, service, archetype, justification, user,
               reason, **arguments):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        dbservice = Service.get_unique(session, name=service, compel=True)

        validate_prod_archetype(dbarchetype, user, justification, reason)

        self._update_dbobj(dbarchetype, dbservice)

        session.flush()
        return
