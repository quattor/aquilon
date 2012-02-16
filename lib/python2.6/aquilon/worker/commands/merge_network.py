# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
from sqlalchemy.sql import and_

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Network, NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.network import fix_foreign_links


class CommandMergeNetwork(BrokerCommand):

    requierd_parameters = ["ip"]

    def render(self, session, dbuser,
               ip, netmask, prefixlen, network_environment, **arguments):
        if netmask:
            # There must me a faster way, but this is the easy one
            net = IPv4Network("127.0.0.0/%s" % netmask)
            prefixlen = net.prefixlen
        if prefixlen is None or prefixlen < 8 or prefixlen > 31:
            raise ArgumentError("The prefix length must be between 8 and 31.")

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        dbnetwork = get_net_id_from_ip(session, ip,
                                       network_environment=dbnet_env)

        if prefixlen >= dbnetwork.cidr:
            raise ArgumentError("The specified --prefixlen must be smaller "
                                "than the current value.")

        # IPv4Network has a supernet() object, but that does not normalize the
        # IP address, i.e. IPv4Network('1.2.3.0/24').supernet() will return
        # IPv4Network('1.2.3.0/23'). Do the normalization manually.
        supernet = dbnetwork.network.supernet(new_prefix=prefixlen)
        supernet = IPv4Network("%s/%d" % (supernet.network, supernet.prefixlen))

        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.filter(and_(Network.ip >= supernet.ip,
                          Network.ip < supernet.broadcast))
        q = q.order_by(Network.ip)
        dbnets = q.all()

        if dbnets[0].ip == supernet.ip:
            dbsuper = dbnets.pop(0)
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

        for oldnet in dbnets:
            # Delete routers of the old subnets
            for dbrouter in oldnet.routers:
                map(delete_dns_record, dbrouter.dns_records)
            oldnet.routers = []

            fix_foreign_links(session, oldnet, dbsuper)
            session.delete(oldnet)

        session.flush()
