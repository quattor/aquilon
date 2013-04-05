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
"""Contains the logic for `aq search dns domain map`."""


from aquilon.aqdb.model import DnsDomain, DnsMap, Location
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location

from sqlalchemy.orm import contains_eager, undefer


class CommandSearchDnsDomainMap(BrokerCommand):

    required_parameters = []

    def render(self, session, dns_domain, include_parents, **kwargs):
        dblocation = get_location(session, **kwargs)
        q = session.query(DnsMap)
        q = q.options(undefer('comments'))
        if dblocation:
            if include_parents:
                location_ids = [parent.id for parent in dblocation.parents]
                location_ids.append(dblocation.id)
                q = q.filter(DnsMap.location_id.in_(location_ids))
            else:
                q = q.filter_by(location=dblocation)
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
            q = q.filter_by(dns_domain=dbdns_domain)

        q = q.join(DnsDomain)
        q = q.options(contains_eager('dns_domain'))
        q = q.join((Location, DnsMap.location_id == Location.id))
        q = q.options(contains_eager('location'))
        q = q.order_by(Location.location_type, Location.name, DnsMap.position)

        return q.all()
