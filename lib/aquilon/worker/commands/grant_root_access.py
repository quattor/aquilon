# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Contains the logic for `aq grant root access`."""

from aquilon.aqdb.model import Personality, User, NetGroupWhiteList
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.personality import PlenaryPersonality
from aquilon.worker.commands.deploy import validate_justification


class CommandGrantRootAccess(BrokerCommand):

    required_parameters = ['personality', 'justification']

    def _update_dbobj(self, obj, dbuser=None, dbnetgroup=None):
        if dbuser and dbuser not in obj.root_users:
            obj.root_users.append(dbuser)
            return
        if dbnetgroup and dbnetgroup not in obj.root_netgroups:
            obj.root_netgroups.append(dbnetgroup)

    def render(self, session, logger, username, netgroup, personality,
               archetype, justification, user, **arguments):

	validate_justification(user, justification)
        dbobj = Personality.get_unique(session, name=personality,
                                       archetype=archetype, compel=True)

        if username:
            dbuser = User.get_unique(session, name=username,
                                     compel=True)
            self._update_dbobj(dbobj, dbuser=dbuser)
        elif netgroup:
            dbng = NetGroupWhiteList.get_unique(session, name=netgroup,
                                                compel=True)
            self._update_dbobj(dbobj, dbnetgroup=dbng)

        session.flush()

        plenary = PlenaryPersonality(dbobj, logger=logger)
        plenary.write()

        return
