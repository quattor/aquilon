# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from ipaddr import IPv4Network

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (Network, NetworkEnvironment, AddressAssignment,
                                ARecord)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.dbwrappers.network import fix_foreign_links


class CommandSplitNetwork(BrokerCommand):

    requierd_parameters = ["ip"]

    def render(self, session, dbuser,
               ip, netmask, prefixlen, network_environment, **arguments):
        if netmask:
            # There must me a faster way, but this is the easy one
            net = IPv4Network("127.0.0.0/%s" % netmask)
            prefixlen = net.prefixlen
        if prefixlen < 8 or prefixlen > 32:
            raise ArgumentError("The prefix length must be between 8 and 32.")

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        dbnetwork = get_net_id_from_ip(session, ip,
                                       network_environment=dbnet_env)

        if prefixlen <= dbnetwork.cidr:
            raise ArgumentError("The specified --prefixlen must be bigger "
                                "than the current value.")

        subnets = dbnetwork.network.subnet(new_prefix=prefixlen)

        # Collect IP addresses that will become network/broadcast addresses
        # after the split
        bad_ips = []
        for subnet in subnets:
            bad_ips.append(subnet.ip)
            bad_ips.append(subnet.broadcast)

        q = session.query(AddressAssignment.ip)
        q = q.filter_by(network=dbnetwork)
        q = q.filter(AddressAssignment.ip.in_(bad_ips))
        used_addrs = q.all()
        if used_addrs:
            raise ArgumentError("Network split failed, because the following "
                                "subnet IP and/or broadcast addresses are "
                                "assigned to hosts: %s" %
                                ", ".join([str(addr.ip) for addr in
                                           used_addrs]))

        q = session.query(ARecord.ip)
        q = q.filter_by(network=dbnetwork)
        q = q.filter(ARecord.ip.in_(bad_ips))
        used_addrs = q.all()
        if used_addrs:
            raise ArgumentError("Network split failed, because the following "
                                "subnet IP and/or broadcast addresses are "
                                "registered in the DNS: %s" %
                                ", ".join([str(addr.ip) for addr in
                                           used_addrs]))

        # Reason of the initial value: we keep the name of the first segment
        # (e.g.  "foo"), and the next segment will be called "foo_2"
        name_idx = 2

        dbnets = []
        for subnet in dbnetwork.network.subnet(new_prefix=prefixlen):
            # Skip the original
            if subnet.ip == dbnetwork.ip:
                continue

            # Generate a new name. Make it unique, even if the DB does not
            # enforce that currently
            while True:
                # TODO: check if the new name is too long
                name = "%s_%d" % (dbnetwork.name, name_idx)
                name_idx += 1
                q = session.query(Network)
                q = q.filter_by(network_environment=dbnet_env)
                q = q.filter_by(name=name)
                if q.count() == 0:
                    break

                # Should not happen...
                if name_idx > 1000:  # pragma: no cover
                    raise AquilonError("Could not generate a unique network "
                                       "name in a reasonable time, bailing out")

            # Inherit location & side from the supernet
            newnet = Network(name=name, network=subnet,
                             network_environment=dbnet_env,
                             location=dbnetwork.location, side=dbnetwork.side,
                             comments="Created by splitting {0:a}".format(dbnetwork))
            session.add(newnet)
            dbnets.append(newnet)

        dbnetwork.cidr = prefixlen
        session.flush()

        for newnet in dbnets:
            fix_foreign_links(session, dbnetwork, newnet)

        session.flush()
