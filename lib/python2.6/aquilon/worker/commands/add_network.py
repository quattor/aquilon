# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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

import math
from ipaddr import IPv4Network, AddressValueError, NetmaskValueError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.aqdb.model import Network, NetworkEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddNetwork(BrokerCommand):

    required_parameters = ["network", "ip"]

    def render(self, session, dbuser,
               network, ip, network_environment, type, side, comments, logger,
               **arguments):

        # Handle the different ways of specifying the netmask
        mask_options = ["netmask", "prefixlen", "mask"]
        numopts = sum([1 if arguments.get(opt, None) else 0
                       for opt in mask_options])
        if numopts != 1:
            raise ArgumentError("Exactly one of --netmask, --prefixlen and "
                                "--mask should be specified.")

        if arguments.get("netmask", None):
            netmask = arguments["netmask"]
        elif arguments.get("prefixlen", None):
            # IPv4Network can handle it just fine
            netmask = arguments["prefixlen"]
        elif arguments.get("mask"):
            netmask = 32 - int(math.log(arguments["mask"], 2))

        try:
            address = IPv4Network("%s/%s" % (ip, netmask))
        except AddressValueError, e:
            raise ArgumentError("Failed to parse the network address: %s" % e)
        except NetmaskValueError, e:
            raise ArgumentError("Failed to parse the netmask: %s" % e)

        if ip != address.network:
            raise ArgumentError("IP address %s is not a network address.  "
                                "Maybe you meant %s?" % (ip, address.network))

        location = get_location(session, **arguments)
        if not type:
            type = 'unknown'
        if not side:
            side = 'a'

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        # Check if the name is free. Network names are not unique in QIP and
        # there is no uniqueness constraint in AQDB, so only warn if the name is
        # already in use.
        q = session.query(Network).filter_by(name=network)
        dbnetwork = q.first()
        if dbnetwork:
            logger.client_info("WARNING: Network name %s is already used for "
                               "address %s." % (network, str(dbnetwork.network)))

        # Check if the address is free
        try:
            dbnetwork = get_net_id_from_ip(session, address.ip,
                                           network_environment=dbnet_env)
            raise ArgumentError("IP address %s is part of existing network "
                                "named %s with address %s." %
                                (str(address.ip), dbnetwork.name,
                                 str(dbnetwork.network)))
        except NotFoundException:
            pass

        # Okay, all looks good, let's create the network
        net = Network(name=network, network=address,
                      network_environment=dbnet_env, network_type=type,
                      side=side, location=location, comments=comments)

        session.add(net)
        session.flush()
        return
