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
"""Contains the logic for `aq add srv record`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Fqdn, SrvRecord, DnsDomain, DnsEnvironment
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611


class CommandAddSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain",
                           "priority", "weight", "target", "port"]

    def render(self, session, service, protocol, dns_domain, priority, weight,
               target, port, dns_environment, comments, **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)
        if dbdns_domain.restricted:
            raise ArgumentError("{0} is restricted, SRV records are not allowed."
                                .format(dbdns_domain))

        # TODO: we could try looking up the port based on the service, but there
        # are some caveats:
        # - the protocol name used in SRV record may not match the name used in
        #   /etc/services
        # - socket.getservent() may return bogus information (like it does for
        #   e.g. 'kerberos')

        service = service.strip().lower()
        target = target.strip().lower()

        dbtarget = Fqdn.get_unique(session, target, compel=True)
        dbsrv_rec = SrvRecord(service=service, protocol=protocol,
                              priority=priority, weight=weight, target=dbtarget,
                              port=port, dns_domain=dbdns_domain,
                              dns_environment=dbdns_env, comments=comments)
        session.add(dbsrv_rec)

        session.flush()

        return
