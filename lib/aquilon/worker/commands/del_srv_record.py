# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016  Contributor
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
"""Contains the logic for `aq del srv record`."""

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import SrvRecord, Fqdn
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record


class CommandDelSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain"]

    def render(self, session, service, protocol, dns_domain, target,
               dns_environment, target_environment, **_):
        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())
        dbfqdn = Fqdn.get_unique(session, name=name, dns_domain=dns_domain,
                                 dns_environment=dns_environment)
        if target:
            if not target_environment:
                target_environment = dns_environment

            dbtarget = Fqdn.get_unique(session, fqdn=target,
                                       dns_environment=target_environment,
                                       compel=True)
        else:
            dbtarget = None

        rrs = []
        if dbfqdn:
            for rr in dbfqdn.dns_records:
                if not isinstance(rr, SrvRecord):  # pragma: no cover
                    # This case can't happen right now. Maybe one day if we
                    # add support for DNSSEC...
                    continue
                if dbtarget and rr.target != dbtarget:
                    continue
                rrs.append(rr)

        if not rrs:
            if dbtarget:
                msg = ", with target %s" % dbtarget.fqdn
            else:
                msg = ""
            raise NotFoundException("%s for service %s, protocol %s in DNS "
                                    "domain %s%s not found." %
                                    (SrvRecord._get_class_label(), service,
                                     protocol, dns_domain, msg))

        for dns_rec in rrs:
            delete_dns_record(dns_rec)
        session.flush()

        return
