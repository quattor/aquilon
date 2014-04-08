# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq update router address`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import RouterAddress, Building, ARecord


class CommandUpdateRouterAddress(BrokerCommand):

    def render(self, session, fqdn, ip, building, comments, **arguments):
        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn, compel=True)
            ip = dbdns_rec.ip
        if not ip:
            raise ArgumentError("Please specify either --ip or --fqdn.")

        router = RouterAddress.get_unique(session, ip=ip, compel=True)

        if building:
            dbbuilding = Building.get_unique(session, name=building,
                                             compel=True)
            router.location = dbbuilding

        if comments is not None:
            router.comments = comments

        session.flush()
