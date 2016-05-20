# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Contains the logic for `aq update address alias`."""

from aquilon.aqdb.model import Fqdn, AddressAlias
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.exceptions_ import ArgumentError


class CommandUpdateAddressAlias(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, logger, fqdn, target, ttl, clear_ttl, comments,
               dns_environment, target_environment, grn, eon_id, clear_grn,
               **_):
        if not target_environment:
            target_environment = dns_environment

        dbfqdn = Fqdn.get_unique(session, fqdn=fqdn,
                                 dns_environment=dns_environment,
                                 compel=True)

        dbdns_records = []
        if target:
            dbtarget = Fqdn.get_unique(session, fqdn=target,
                                       dns_environment=target_environment,
                                       compel=True)

            dbaddr_alias = AddressAlias.get_unique(session, fqdn=dbfqdn,
                                                   target=dbtarget, compel=True)
            dbdns_records.append(dbaddr_alias)
        else:
            dbdns_records = [rec for rec in dbfqdn.dns_records if isinstance(rec, AddressAlias)]
            if len(dbdns_records) == 0:
                raise ArgumentError("No address alias record found.")

        dbgrn = None
        update_grn = False
        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            update_grn = True
        elif clear_grn:
            update_grn = True

        for dbaddr_alias in dbdns_records:
            if ttl is not None:
                dbaddr_alias.ttl = ttl
            elif clear_ttl:
                dbaddr_alias.ttl = None

            if update_grn:
                dbaddr_alias.owner_grn = dbgrn

            if comments is not None:
                dbaddr_alias.comments = comments

        session.flush()
        return
