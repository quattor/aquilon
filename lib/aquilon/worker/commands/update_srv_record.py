# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016,2017  Contributor
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
"""Contains the logic for `aq update srv record`."""

from sqlalchemy.orm import contains_eager

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Fqdn, SrvRecord, DnsDomain, DnsEnvironment
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain"]

    def render(self, session, logger, service, protocol, dns_domain, target,
               priority, weight, port, ttl, clear_ttl, comments,
               dns_environment, grn, eon_id, clear_grn, user,
               justification, reason, **arguments):
        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

        dbdns_records = []
        if target:
            dbsrv_rec = SrvRecord.get_unique(session, name=name,
                                             dns_domain=dbdns_domain,
                                             dns_environment=dbdns_env,
                                             target=target, compel=True)
            dbdns_records.append(dbsrv_rec)
        else:
            records = self.get_records_in_rrset(session, name,
                                                dbdns_domain, dbdns_env)
            dbdns_records.extend(records)
            if len(dbdns_records) == 0:
                raise ArgumentError("No SRV record found.")

        dbgrn = None
        update_grn = False
        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            update_grn = True
        elif clear_grn:
            update_grn = True

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        for dbsrv_rec in dbdns_records:
            cm.consider(dbsrv_rec.fqdn)

            if priority:
                dbsrv_rec.priority = priority
            if weight:
                dbsrv_rec.weight = weight
            if port:
                dbsrv_rec.port = port

            if ttl is not None:
                dbsrv_rec.ttl = ttl
            elif clear_ttl:
                dbsrv_rec.ttl = None

            if update_grn:
                dbsrv_rec.owner_grn = dbgrn

            if comments is not None:
                dbsrv_rec.comments = comments

        cm.validate()

        session.flush()
        return

    def get_records_in_rrset(self, session, name, dbdns_domain,
                             dbdns_env):

        q = session.query(SrvRecord)
        q = q.join((Fqdn, SrvRecord.fqdn_id == Fqdn.id))
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_domain=dbdns_domain)
        q = q.filter_by(name=name)
        q = q.filter_by(dns_environment=dbdns_env)

        return q.all()
