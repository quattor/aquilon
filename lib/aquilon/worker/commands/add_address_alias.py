# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
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
"""Contains the logic for `aq add address alias`."""

from aquilon.aqdb.model import (
    Fqdn,
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.dns import add_address_alias


class CommandAddAddressAlias(BrokerCommand):

    required_parameters = ["fqdn", "target"]

    def render(self, session, logger, fqdn, dns_environment, target,
               target_environment, ttl, grn, eon_id, comments, exporter,
               user, justification, reason, **arguments):

        if not target_environment:
            target_environment = dns_environment

        dbfqdn = Fqdn.get_or_create(session, dns_environment=dns_environment,
                                    fqdn=fqdn)

        dbtarget = Fqdn.get_unique(session, fqdn=target,
                                   dns_environment=target_environment,
                                   compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbtarget)
        cm.validate()

        add_address_alias(session, logger, config=self.config,
                          dbsrcfqdn=dbfqdn,
                          dbtargetfqdn=dbtarget,
                          ttl=ttl, grn=grn, eon_id=eon_id,
                          comments=comments, exporter=exporter,
                          flush_session=True)

        return
