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
"""Contains the logic for `aq update alias`."""

from aquilon.aqdb.model import Alias, DnsEnvironment
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import (create_target_if_needed,
                                           delete_target_if_needed)
from aquilon.worker.processes import DSDBRunner


class CommandUpdateAlias(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, logger, fqdn, dns_environment, target, comments,
               **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbalias = Alias.get_unique(session, fqdn=fqdn,
                                   dns_environment=dbdns_env, compel=True)

        old_target_fqdn = str(dbalias.target.fqdn)
        old_comments = dbalias.comments

        if target:
            old_target = dbalias.target
            dbalias.target = create_target_if_needed(session, logger,
                                                     target, dbdns_env)
            if dbalias.target != old_target:
                delete_target_if_needed(session, old_target)

        if comments is not None:
            dbalias.comments = comments

        session.flush()

        if dbdns_env.is_default and dbalias.fqdn.dns_domain.name == "ms.com":
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_alias(fqdn, dbalias.target.fqdn,
                                     dbalias.comments, old_target_fqdn,
                                     old_comments)
            dsdb_runner.commit_or_rollback("Could not update alias in DSDB")

        return
