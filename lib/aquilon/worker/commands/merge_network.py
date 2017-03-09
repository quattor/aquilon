# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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

from ipaddress import IPv4Network

from sqlalchemy.sql import and_

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Network, NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.network import fix_foreign_links


class CommandMergeNetwork(BrokerCommand):
    requires_plenaries = True

    requierd_parameters = ["ip"]

    def render(self, session, plenaries, dbuser,
               ip, netmask, prefixlen, network_environment, **_):
        if netmask:
            # There must me a faster way, but this is the easy one
            net = IPv4Network(u"127.0.0.0/%s" % netmask)
            prefixlen = net.prefixlen

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        dbnetwork = get_net_id_from_ip(session, ip,
                                       network_environment=dbnet_env)

        if prefixlen >= dbnetwork.cidr:
            raise ArgumentError("The specified --prefixlen must be smaller "
                                "than the current value.")

        supernet = dbnetwork.network.supernet(new_prefix=prefixlen)

        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.filter(and_(Network.ip >= supernet.network_address,
                          Network.ip < supernet.broadcast_address))
        q = q.order_by(Network.ip)
        dbnets = q.all()

        if dbnets[0].ip == supernet.network_address:
            dbsuper = dbnets.pop(0)
            plenaries.add(dbsuper)
            dbsuper.cidr = prefixlen
        else:
            # Create a new network, copying the parameters from the one
            # specified on the command line
            dbsuper = Network(name=dbnetwork.name, network=supernet,
                              network_environment=dbnet_env,
                              location=dbnetwork.location,
                              side=dbnetwork.side,
                              comments=dbnetwork.comments)
            session.add(dbsuper)
            plenaries.add(dbsuper)

        for oldnet in dbnets:
            plenaries.add(oldnet)

            # Delete routers of the old subnets
            for dbrouter in oldnet.routers:
                for dns_rec in dbrouter.dns_records:
                    delete_dns_record(dns_rec)
            oldnet.routers = []

            fix_foreign_links(session, oldnet, dbsuper)
            session.delete(oldnet)

        session.flush()
        plenaries.write()
