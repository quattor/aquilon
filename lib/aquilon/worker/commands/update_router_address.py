# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq update router address`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import RouterAddress, Building, ARecord
from aquilon.aqdb.model.network_environment import get_net_dns_env
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates import PlenaryCollection


class CommandUpdateRouterAddress(BrokerCommand):

    def render(self, session, logger, fqdn, ip, building, clear_location,
               network_environment, dns_environment, comments, **_):
        dbnet_env, dbdns_env = get_net_dns_env(session, network_environment,
                                               dns_environment)
        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                           dns_environment=dbdns_env,
                                           compel=True)
            ip = dbdns_rec.ip
        if not ip:
            raise ArgumentError("Please specify either --ip or --fqdn.")

        dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
        router = RouterAddress.get_unique(session, ip=ip, network=dbnetwork,
                                          compel=True)

        if building:
            dbbuilding = Building.get_unique(session, name=building,
                                             compel=True)
            router.location = dbbuilding
        elif clear_location:
            router.location = None

        if comments is not None:
            router.comments = comments

        # Refresh the plenaries even if nothing in the DB has changed
        plenaries = PlenaryCollection(logger=logger)
        plenaries.add(dbnetwork)
        plenaries.write()

        session.flush()
