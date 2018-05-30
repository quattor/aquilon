# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Contains the logic for `aq show permission `."""

import getpass

from aquilon.aqdb.model import UserPrincipal, Realm
from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError


class CommandShowPermission(BrokerCommand):

    def render(self, session, **arguments):
        username = getpass.getuser()
        q = session.query(UserPrincipal)
        q = q.filter_by(name=username)
        if q.count() > 1:
            raise ArgumentError("More than one user found for this name: '{}' "
                                "please try to specify a realm with "
                                "show_permission --username USER --realm REALM"
                                .format(username))
        elif not q.count():
            raise ArgumentError("User {} not found".format(username))
        return self.az.check_role_permission(session, str(q.first().role))
