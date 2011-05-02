# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.

from ipaddr import IPv4Network
from sqlalchemy.sql import or_

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import (Network, NetworkEnvironment, AddressAssignment,
                                ARecord)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.server.dbwrappers.network import fix_foreign_links


class CommandSplitNetwork(BrokerCommand):

    requierd_parameters = ["ip"]

    def render(self, session, ip, netmask, prefixlen, network_environment,
               **arguments):
        if netmask:
            # There must me a faster way, but this is the easy one
            net = IPv4Network("127.0.0.0/%s" % netmask)
            prefixlen = net.prefixlen
        if prefixlen < 8 or prefixlen > 32:
            raise ArgumentError("The prefix length must be between 8 and 32.")

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

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
            # TODO: what to do with the discovered/discoverable flags?
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
