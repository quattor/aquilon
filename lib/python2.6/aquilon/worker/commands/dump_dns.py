# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Contains the logic for `aq dump dns`."""

from sqlalchemy.orm import contains_eager

from aquilon.aqdb.model import DnsRecord, Fqdn, DnsDomain, DnsEnvironment
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.dns_record import DnsDump


class CommandDumpDns(BrokerCommand):

    default_style = "djb"
    requires_format = True
    requires_readonly = True

    def render(self, session, dns_domain, dns_environment, **arguments):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
        else:
            dbdns_domain = None

        q = session.query(DnsRecord)
        q = q.with_polymorphic('*')
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_environment=dbdns_env)
        if dbdns_domain:
            q = q.filter_by(dns_domain=dbdns_domain)
            dns_domains = [dbdns_domain]
        else:
            # Preload DNS domains, and keep a reference to prevent them being
            # evicted from the session's cache
            dns_domains = session.query(DnsDomain).all()

        return DnsDump(q.all(), dns_domains)
