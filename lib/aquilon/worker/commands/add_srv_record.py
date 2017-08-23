# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Fqdn, SrvRecord, DnsDomain, DnsEnvironment,
                                ReservedName)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import create_target_if_needed
from aquilon.worker.dbwrappers.grn import lookup_grn


class CommandAddSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain",
                           "priority", "weight", "target", "port"]

    def render(self, session, logger, service, protocol, dns_domain, priority,
               weight, target, port, dns_environment, ttl, comments, grn,
               eon_id, target_environment, exporter, **_):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)

        if target_environment:
            dbtgt_env = DnsEnvironment.get_unique(session, target_environment)
        else:
            dbtgt_env = dbdns_env

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

        name = "_%s._%s" % (service, protocol)

        dbgrn = None
        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)

        # Make sure the GRN of the SRV record is consistent across the rrset
        curr_rec = self.get_first_srv_record(session, name, dbdns_domain,
                                             dbdns_env)
        if curr_rec:
            if not dbgrn:
                dbgrn = curr_rec.owner_grn
            elif dbgrn != curr_rec.owner_grn:
                raise ArgumentError("{0} with target {1} is set to a "
                                    "different GRN."
                                    .format(curr_rec.fqdn, curr_rec.target.fqdn))

        dbtarget = create_target_if_needed(session, logger, target, dbtgt_env)
        dbsrv_rec = SrvRecord(service=service, protocol=protocol,
                              priority=priority, weight=weight, target=dbtarget,
                              port=port, dns_domain=dbdns_domain, ttl=ttl,
                              dns_environment=dbdns_env, comments=comments,
                              owner_grn=dbgrn)
        session.add(dbsrv_rec)

        if exporter:
            if any(
                    dr != dbsrv_rec and
                    not isinstance(dr, ReservedName)
                    for dr in dbsrv_rec.fqdn.dns_records):
                exporter.update(dbsrv_rec.fqdn)
            else:
                exporter.create(dbsrv_rec.fqdn)


        session.flush()

        return

    def get_first_srv_record(self, session, name, dbdns_domain, dbdns_env):
        q = session.query(SrvRecord)
        q = q.join((Fqdn, SrvRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_domain=dbdns_domain)
        q = q.filter_by(name=name)
        q = q.filter_by(dns_environment=dbdns_env)

        return q.first()
