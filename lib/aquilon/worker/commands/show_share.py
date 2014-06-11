# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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

from sqlalchemy.orm import undefer

from aquilon.aqdb.model import Share
from aquilon.aqdb.data_sync.storage import StormapParser
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import get_resource_holder


class CommandShowShare(BrokerCommand):

    required_parameters = []

    def render(self, session, share, hostname, resourcegroup, cluster, all,
               **arguments):
        q = session.query(Share)
        if share:
            q = q.filter_by(name=share)

        q = q.options(undefer(Share.virtual_disk_count),
                      undefer(Share.virtual_machine_count))

        if hostname or cluster or resourcegroup:
            who = get_resource_holder(session, hostname, cluster, resourcegroup)
            q = q.filter_by(holder=who)

        shares = q.all()

        parser = StormapParser()
        for dbshare in shares:
            dbshare.populate_share_info(parser)

        return shares
