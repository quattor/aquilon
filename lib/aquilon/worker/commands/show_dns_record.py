# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016  Contributor
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
"""Contains the logic for `aq show dns record`."""

from sqlalchemy.orm import undefer, lazyload
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import DnsRecord, ARecord, Alias, SrvRecord, Fqdn
from aquilon.aqdb.model.network_environment import get_net_dns_env
from aquilon.worker.broker import BrokerCommand


DNS_RRTYPE_MAP = {'a': ARecord,
                  'cname': Alias,
                  'srv': SrvRecord}


class CommandShowDnsRecord(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, fqdn, record_type, dns_environment,
               network_environment=None, **_):
        _, dbdns_env = get_net_dns_env(session, network_environment,
                                       dns_environment)

        # No compel here. query(DnsRecord).filter_by(fqdn=None) will fail if the
        # FQDN is invalid, and that will give a better error message.
        dbfqdn = Fqdn.get_unique(session, fqdn=fqdn, dns_environment=dbdns_env)

        # We want to query(ARecord) instead of
        # query(DnsRecord).filter_by(record_type='a_record'), because the former
        # works for DynamicStub as well
        if record_type:
            if record_type in DNS_RRTYPE_MAP:
                cls = DNS_RRTYPE_MAP[record_type]
            else:
                cls = DnsRecord.polymorphic_subclass(record_type,
                                                     "Unknown DNS record type")
            q = session.query(cls)
        else:
            cls = DnsRecord
            q = session.query(cls)
            q = q.with_polymorphic('*')

        q = q.options(undefer('comments'),
                      lazyload('fqdn'))
        q = q.filter_by(fqdn=dbfqdn)
        result = q.all()
        if not result:
            raise NotFoundException("%s %s not found." %
                                    (cls._get_class_label(), fqdn))

        for res in result:
            set_committed_value(res, 'fqdn', dbfqdn)
        return result
