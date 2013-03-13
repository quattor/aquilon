# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq del router`."""

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.aqdb.model import ARecord, NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandDelRouter(BrokerCommand):

    required_parameters = []

    def render(self, session, dbuser,
               ip, fqdn, network_environment, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)
        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                           dns_environment=dbnet_env.dns_environment,
                                           compel=True)
            ip = dbdns_rec.ip
        elif not ip:
            raise ArgumentError("Please specify either --ip or --fqdn.")

        dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
        dbrouter = None
        for rtaddr in dbnetwork.routers:
            if rtaddr.ip == ip:
                dbrouter = rtaddr
                break
        if not dbrouter:
            raise NotFoundException("IP address {0} is not a router on "
                                    "{1:l}.".format(ip, dbnetwork))

        map(delete_dns_record, dbrouter.dns_records)
        dbnetwork.routers.remove(dbrouter)
        session.flush()

        # TODO: update the templates of Zebra hosts on the network

        return
