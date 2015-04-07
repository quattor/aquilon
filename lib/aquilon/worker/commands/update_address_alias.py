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
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611


class CommandUpdateAddressAlias(BrokerCommand):

    required_parameters = ["fqdn", "target"]

    def render(self, session, fqdn, target, ttl, clear_ttl, comments,
               dns_environment, target_environment, **kwargs):
        if not target_environment:
            target_environment = dns_environment

        dbfqdn = Fqdn.get_unique(session, fqdn=fqdn,
                                 dns_environment=dns_environment,
                                 compel=True)

        dbtarget = Fqdn.get_unique(session, fqdn=target,
                                   dns_environment=target_environment,
                                   compel=True)

        dbaddr_alias = AddressAlias.get_unique(session, fqdn=dbfqdn,
                                               target=dbtarget, compel=True)

        if ttl is not None:
            dbaddr_alias.ttl = ttl
        elif clear_ttl:
            dbaddr_alias.ttl = None

        if comments is not None:
            dbaddr_alias.comments = comments

        session.flush()
        return
