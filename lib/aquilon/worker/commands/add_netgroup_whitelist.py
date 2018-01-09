# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2016,2017  Contributor
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
"""Contains the logic for `aq add netgroup whitelist`."""

from aquilon.aqdb.model import NetGroupWhiteList
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddNetgroupWhitelist(BrokerCommand):

    required_parameters = ["netgroup"]

    def render(self, session, netgroup, user, justification,
               reason, logger, **arguments):
        NetGroupWhiteList.get_unique(session, name=netgroup, preclude=True)
        dbng = NetGroupWhiteList(name=netgroup)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbng)
        cm.validate()

        session.add(dbng)

        session.flush()
        return
