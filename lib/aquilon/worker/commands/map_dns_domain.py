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
""" Map DNS domains to locations """

from sqlalchemy.orm import subqueryload

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import DnsDomain, DnsMap
from aquilon.worker.dbwrappers.location import get_location


class CommandMapDnsDomain(BrokerCommand):

    required_parameters = ["dns_domain"]

    def render(self, session, dns_domain, position, comments, **kw):
        dbdns_domain = DnsDomain.get_unique(session, name=dns_domain,
                                            compel=True)

        dblocation = get_location(session,
                                  query_options=[subqueryload('dns_maps')],
                                  **kw)
        if not dblocation:
            raise ArgumentError("Please specify a location.")

        DnsMap.get_unique(session, dns_domain=dbdns_domain, location=dblocation,
                          preclude=True)

        dbmap = DnsMap(dns_domain=dbdns_domain, comments=comments)
        if position is not None:
            dblocation.dns_maps.insert(position, dbmap)
        else:
            dblocation.dns_maps.append(dbmap)

        session.flush()
        return
