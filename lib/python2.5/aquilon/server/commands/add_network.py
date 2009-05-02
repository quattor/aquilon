# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon

from sqlalchemy.exceptions import InvalidRequestError
from twisted.python import log

from aquilon.exceptions_ import (ArgumentError, NotFoundException)
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.aqdb.net.network import Network, _mask_to_cidr, get_bcast
import re

class CommandAddNetwork(BrokerCommand):

    required_parameters = [ "network", "ip", "mask" ]

    def render(self, session, network, mask, discovered, discoverable, ip, type, side, **arguments):

        location = get_location(session, **arguments)
        if not type:
            type = 'unknown'
        if not side:
            side = 'a'

        try:
            dbnetwork = network and get_network_byname(session, network) or None
            dbnetwork = ip and get_network_byip(session, ip) or dbnetwork
            if dbnetwork:
                raise ArgumentError('Network already exists')
        except NotFoundException, e:
            pass

        yes = re.compile("^(true|yes|y|1|on|enabled)$", re.I)
        no = re.compile("^(false|no|n|0|off|disabled)$", re.I)
        if discovered:
            if yes.match(discovered):
                discovered = "y"
            elif no.match(discovered):
                discovered = "n"
            else:
                raise ArgumentError('Did not recognise supplied argument to discovered flag: "%s"' % discovered)
        if discoverable:
            if yes.match(discoverable):
                discoverable = "y"
            elif no.match(discoverable):
                discoverable = "n"
            else:
                raise ArgumentError('Did not recognise supplied argument to discoverable flag: "%s"' % discoverable)

        # Okay, all looks good, let's create the network
        c = _mask_to_cidr[mask]
        net = Network(name         = network,
                      ip           = ip,
                      mask         = mask,
                      cidr         = c,
                      bcast        = get_bcast(ip, c),
                      network_type = type,
                      side         = side,
                      location     = location)

        if discoverable:
            if discoverable == "y":
                net.is_discoverable = True
            elif discoverable == "n":
                net.is_discoverable = False
        if discovered:
            if discovered == "y":
                net.is_discovered = True
            elif discovered == "n":
                net.is_discovered = False
