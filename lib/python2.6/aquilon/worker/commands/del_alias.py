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
"""Contains the logic for `aq del alias`."""

from aquilon.aqdb.model import DnsEnvironment, Alias
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.processes import DSDBRunner


class CommandDelAlias(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, logger, fqdn, dns_environment, **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_rec = Alias.get_unique(session, fqdn=fqdn,
                                     dns_environment=dbdns_env, compel=True)
        domain = dbdns_rec.fqdn.dns_domain.name

        old_target_fqdn = str(dbdns_rec.target)
        old_comments = dbdns_rec.comments
        target_is_restricted = dbdns_rec.target.dns_domain.restricted
        delete_dns_record(dbdns_rec)

        session.flush()

        if dbdns_env.is_default and domain == "ms.com" and not target_is_restricted:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.del_alias(fqdn, old_target_fqdn, old_comments)
            dsdb_runner.commit_or_rollback("Could not delete alias from DSDB")

        return
