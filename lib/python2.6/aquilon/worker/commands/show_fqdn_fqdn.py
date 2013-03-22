# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show fqdn --fqdn`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import DnsEnvironment, Fqdn, DnsRecord


class CommandShowFqdnFqdn(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, fqdn, dns_environment, **kwargs):
        self.deprecated_command("The show_fqdn command is deprecated.  Please "
                                "use search_dns instead.", **kwargs)
        dbdns_env = DnsEnvironment.get_unique_or_default(session, dns_environment)
        dbfqdn = Fqdn.get_unique(session, fqdn=fqdn, dns_environment=dbdns_env,
                                 compel=True)
        q = session.query(DnsRecord)
        q = q.filter_by(fqdn=dbfqdn)
        return q.all()
