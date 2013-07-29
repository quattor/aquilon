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
"""Contains the logic for `aq show srv record`."""


from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import SrvRecord, DnsDomain, DnsEnvironment, Fqdn


class CommandShowSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain"]

    def render(self, session, service, protocol, dns_domain, dns_environment,
               **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())

        q = session.query(SrvRecord)
        q = q.join((Fqdn, SrvRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_domain=dbdns_domain)
        q = q.filter_by(name=name)
        q = q.filter_by(dns_environment=dbdns_env)
        result = q.all()
        if not result:
            raise NotFoundException("%s for service %s, protocol %s in DNS "
                                    "domain %s not found." %
                                    (SrvRecord._get_class_label(), service,
                                     protocol, dns_domain))
        return result
