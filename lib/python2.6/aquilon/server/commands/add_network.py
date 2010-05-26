# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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

import re
from ipaddr import (IPv4Network, IPv4IpValidationError,
                    IPv4NetmaskValidationError)

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname
from aquilon.aqdb.model.network import (Network, _mask_to_cidr,
                                        get_net_id_from_ip)

class CommandAddNetwork(BrokerCommand):

    required_parameters = ["network", "ip"]

    def render(self, session, network, ip, discovered, discoverable, type, side, **arguments):

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
            netmask = _mask_to_cidr[arguments["mask"]]

        try:
            address = IPv4Network("%s/%s" % (ip, netmask))
        except IPv4IpValidationError, e:
            raise ArgumentError("Failed to parse the network address: %s" % e)
        except IPv4NetmaskValidationError, e:
            raise ArgumentError("Failed to parse the netmask: %s" % e)

        location = get_location(session, **arguments)
        if not type:
            type = 'unknown'
        if not side:
            side = 'a'

        # Check if the name is free
        try:
            dbnetwork = get_network_byname(session, network)
            raise ArgumentError("Network name %s is already used for "
                                "address %s." %
                                (network, str(dbnetwork.network)))
        except NotFoundException:
            pass

        # Check if the address is free
        try:
            dbnetwork = get_net_id_from_ip(session, address.ip)
            raise ArgumentError("IP address %s is part of existing network "
                                "named %s with address %s." %
                                (str(address.ip), dbnetwork.name,
                                 str(dbnetwork.network)))
        except NotFoundException:
            pass

        # Okay, all looks good, let's create the network
        net = Network(name         = network,
                      network      = address,
                      network_type = type,
                      side         = side,
                      location     = location)

        if discoverable is not None:
            net.is_discoverable = discoverable
        if discovered is not None:
            net.is_discovered = discovered

        session.add(net)
        session.flush()
        return
