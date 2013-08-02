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
"""Contains the logic for `aq show dns record`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (DnsRecord, ARecord, Alias, SrvRecord,
                                DnsEnvironment, NetworkEnvironment,
                                Fqdn)


DNS_RRTYPE_MAP = {'a': ARecord,
                  'cname': Alias,
                  'srv': SrvRecord}


class CommandShowDnsRecord(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, fqdn, record_type, dns_environment,
               network_environment=None, **arguments):

        if network_environment:
            if not isinstance(network_environment, NetworkEnvironment):
                network_environment = NetworkEnvironment.get_unique_or_default(session,
                                                                               network_environment)
            if not dns_environment:
                dns_environment = network_environment.dns_environment

        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        # No compel here. query(DnsRecord).filter_by(fqdn=None) will fail if the
        # FQDN is invalid, and that will give a better error message.
        dbfqdn = Fqdn.get_unique(session, fqdn=fqdn,
                                 dns_environment=dbdns_env)

        if record_type:
            if record_type in DNS_RRTYPE_MAP:
                cls = DNS_RRTYPE_MAP[record_type]
            else:
                cls = DnsRecord.polymorphic_subclass(record_type,
                                                     "Unknown DNS record type")
        else:
            cls = DnsRecord

        # We want to query(ARecord) instead of
        # query(DnsRecord).filter_by(record_type='a_record'), because the former
        # works for DynamicStub as well
        q = session.query(cls)
        if cls == DnsRecord:
            q = q.with_polymorphic('*')
        q = q.filter_by(fqdn=dbfqdn)
        result = q.all()
        if not result:
            raise NotFoundException("%s %s not found." %
                                    (cls._get_class_label(), fqdn))
        return result
