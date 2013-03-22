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
"""Contains the logic for `aq add dns_domain`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import DSDBRunner
from aquilon.aqdb.model import DnsDomain, Fqdn


class CommandDelDnsDomain(BrokerCommand):

    required_parameters = ["dns_domain"]

    def render(self, session, logger, dns_domain, **arguments):
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

        q = session.query(Fqdn)
        q = q.filter_by(dns_domain=dbdns_domain)
        if q.first():
            raise ArgumentError("DNS domain %s cannot be deleted while still "
                                "in use." % dns_domain)

        if dbdns_domain.dns_maps:
            raise ArgumentError("{0} is still mapped to locations and cannot "
                                "be deleted.".format(dbdns_domain))

        comments = dbdns_domain.comments
        session.delete(dbdns_domain)
        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.delete_dns_domain(dns_domain, comments)
        dsdb_runner.commit_or_rollback()

        return
