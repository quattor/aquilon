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
"""Contains the logic for `aq revoke root access`."""

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.commands.grant_root_access import CommandGrantRootAccess


class CommandRevokeRootAccess(CommandGrantRootAccess):

    def _update_dbobj(self, obj, dbuser=None, dbnetgroup=None):
        if dbuser and dbuser in obj.root_users:
            obj.root_users.remove(dbuser)
            return
        if dbnetgroup and dbnetgroup in obj.root_netgroups:
            obj.root_netgroups.remove(dbnetgroup)
            return
