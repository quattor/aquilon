# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011-2013,2016,2019  Contributor
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

from aquilon.aqdb.model import (
    DnsDomain,
    DnsRecord,
    Fqdn,
    Network,
)
from aquilon.aqdb.model.network_environment import get_net_dns_envs
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.dns_record import DnsDump

from sqlalchemy.sql import (
    and_,
    or_,
)


class CommandDumpDns(BrokerCommand):

    default_style = "djb"
    requires_format = True
    requires_readonly = True

    def render(self, session, dns_domain, **kwargs):
        # Get the network and dns environments to filter with
        dbnet_envs, dbnet_envs_excl, dbdns_envs, dbdns_envs_excl = \
            get_net_dns_envs(session,
                             mandatory_network_environment=False,
                             **kwargs)

        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
        else:
            dbdns_domain = None

        q = session.query(DnsRecord)
        q = q.with_polymorphic('*')
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))

        # Filter using the dns environments, unless selecting all
        if dbdns_envs:
            q = q.filter(or_(Fqdn.dns_environment == dbdnsenv
                             for dbdnsenv in dbdns_envs))
        if dbdns_envs_excl:
            q = q.filter(and_(Fqdn.dns_environment != dbdnsenv
                              for dbdnsenv in dbdns_envs_excl))

        # If there is a need to filter by network environments
        if dbnet_envs or dbnet_envs_excl:
            q = q.outerjoin(Network, aliased=True)
            if dbnet_envs:
                q = q.filter(or_(Network.network_environment == dbnetenv
                                 for dbnetenv in dbnet_envs))
            if dbnet_envs_excl:
                q = q.filter(and_(Network.network_environment != dbnetenv
                                  for dbnetenv in dbnet_envs_excl))
            q = q.reset_joinpoint()

        if dbdns_domain:
            q = q.filter_by(dns_domain=dbdns_domain)
            dns_domains = [dbdns_domain]
        else:
            # Preload DNS domains, and keep a reference to prevent them being
            # evicted from the session's cache
            dns_domains = session.query(DnsDomain).all()

        return DnsDump(q.all(), dns_domains)
