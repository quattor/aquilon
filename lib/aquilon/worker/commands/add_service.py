# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2016  Contributor
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
"""Contains the logic for `aq add service`."""

from aquilon.exceptions_ import AuthorizationException
from aquilon.aqdb.model import Service
from aquilon.worker.broker import BrokerCommand


class CommandAddService(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["service"]

    def render(self, session, plenaries, dbuser, service, need_client_list,
               allow_alias_bindings, comments, **_):
        Service.get_unique(session, service, preclude=True)

        if dbuser.role.name != 'aqd_admin' and allow_alias_bindings is not None:
            raise AuthorizationException("Only AQD admin can set allowing alias bindings")

        dbservice = Service(name=service, comments=comments,
                            need_client_list=need_client_list, allow_alias_bindings=allow_alias_bindings)
        session.add(dbservice)

        plenaries.add(dbservice)

        session.flush()
        plenaries.write()
        return
