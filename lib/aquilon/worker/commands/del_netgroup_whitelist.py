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
"""Contains the logic for `aq del netgroup whitelist`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import NetGroupWhiteList, Personality
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import Plenary, PlenaryCollection
from sqlalchemy.orm import subqueryload, joinedload


class CommandDelNetgroupWhitelist(BrokerCommand):

    required_parameters = ["netgroup"]

    def render(self, session, logger, netgroup, **arguments):
        dbng = NetGroupWhiteList.get_unique(session, name=netgroup,
                                            compel=True)

        plenaries = PlenaryCollection(logger=logger)

        q = session.query(Personality)
        q = q.filter(Personality.root_netgroups.contains(dbng))
        pers = q.all()

        if pers:
            raise ArgumentError("Netgroup {0} used by following and cannot be deleted: ".
                                format(netgroup) + ", ".join(["{0}".format(p) for p in pers]))

        session.delete(dbng)
        session.flush()

        plenaries.write()
