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
"""Contains the logic for `aq show netgroup whitelist`."""

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import NetGroupWhiteList
from aquilon.worker.broker import BrokerCommand


class CommandShowNetgroupWhitelist(BrokerCommand):

    def render(self, session, netgroup, all, **arguments):
        q = session.query(NetGroupWhiteList)
        if netgroup:
            q = q.filter_by(name=netgroup)
        result = q.all()
        if not result:
            if netgroup:
                raise NotFoundException("Netgroup %s not found." % netgroup)
        return result
