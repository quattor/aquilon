# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016  Contributor
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
"""Contains the logic for `aq update service`."""

from aquilon.aqdb.model import Service
from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import AuthorizationException


class CommandUpdateService(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["service"]

    def render(self, session, logger, plenaries, dbuser, service, max_clients, default,
               need_client_list, allow_alias_bindings, comments, **_):
        dbservice = Service.get_unique(session, name=service, compel=True)

        if dbuser.role.name != 'aqd_admin' and allow_alias_bindings is not None:
            raise AuthorizationException("Only AQD admin can set allowing alias bindings")

        if default:
            dbservice.max_clients = None
        elif max_clients is not None:
            dbservice.max_clients = max_clients

        if need_client_list is not None:
            dbservice.need_client_list = need_client_list

        if comments is not None:
            dbservice.comments = comments

        if allow_alias_bindings is not None:
            dbservice.allow_alias_bindings = allow_alias_bindings

        session.flush()

        plenaries.add(dbservice)
        plenaries.add(dbservice.instances)
        plenaries.write()

        return
