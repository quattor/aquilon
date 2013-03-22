# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq search domain`."""

from aquilon.aqdb.model import Branch, Domain
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.branch import search_branch_query
from aquilon.worker.formats.list import StringList


class CommandSearchDomain(BrokerCommand):

    def render(self, session, track, change_manager, fullinfo, **arguments):
        q = search_branch_query(self.config, session, Domain, **arguments)
        if track:
            dbtracked = Branch.get_unique(session, track, compel=True)
            q = q.filter_by(tracked_branch=dbtracked)
        if change_manager is not None:
            q = q.filter_by(requires_change_manager=change_manager)

        q = q.order_by(Domain.name)
        result = q.all()

        if fullinfo:
            return result
        else:
            return StringList(result)
