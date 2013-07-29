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
"""Contains a wrapper for `aq add host --prefix`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_host import CommandAddHost
from aquilon.worker.dbwrappers.search import search_next
from aquilon.aqdb.model import Machine, DnsDomain, Fqdn
from aquilon.aqdb.column_types import AqStr


class CommandAddHostPrefix(CommandAddHost):

    required_parameters = ["prefix", "machine", "archetype"]

    def render(self, session, logger, prefix, dns_domain, hostname, machine,
               **args):
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
        else:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            dbdns_domain = None
            loc = dbmachine.location
            while loc and not dbdns_domain:
                dbdns_domain = loc.default_dns_domain
                loc = loc.parent

            if not dbdns_domain:
                raise ArgumentError("There is no default DNS domain configured "
                                    "for the machine's location. Please "
                                    "specify --dns_domain.")

        # Lock the DNS domain to prevent the same name generated for
        # simultaneous requests
        dbdns_domain.lock_row()

        prefix = AqStr.normalize(prefix)
        result = search_next(session=session, cls=Fqdn, attr=Fqdn.name,
                             value=prefix, dns_domain=dbdns_domain,
                             start=None, pack=None)
        hostname = "%s%d.%s" % (prefix, result, dbdns_domain)

        CommandAddHost.render(self, session, logger, hostname=hostname,
                              machine=machine, **args)

        logger.info("Selected host name %s" % hostname)
        self.audit_result(session, 'hostname', hostname, **args)
        return hostname
