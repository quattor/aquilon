# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2016,2018  Contributor
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
"""Contains the logic for `aq show permission --role`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand

from aquilon.aqdb.model import Role


class CommandShowPermissionRole(BrokerCommand):

    required_parameters = ["role"]

    def render(self, session, role, **arguments):

        if not session.query(Role).filter(Role.name == role).count():
            raise ArgumentError("{} role doesn't exist".format(role))
        return self.az.check_role_permission(session, role)
