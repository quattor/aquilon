# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show network`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Interface, Network
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.server.formats.network import SimpleNetworkList
from aquilon.server.formats.network import NetworkHostList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, all, discovered, discoverable, type=False, hosts=False, **arguments):
        dbnetwork = network and get_network_byname(session, network) or None
        dbnetwork = ip and get_network_byip(session, ip) or dbnetwork
        q = session.query(Network)
        if dbnetwork:
            if hosts:
                return NetworkHostList([dbnetwork])
            else:
                return dbnetwork
        if type:
            q = q.filter_by(network_type = type)
        if discoverable:
            q = q.filter_by(is_discoverable = True)
        if discovered:
            q = q.filter_by(is_discovered = True)
        dblocation = get_location(session, **arguments)
        if dblocation:
            q = q.filter_by(location=dblocation)
        if hosts:
            return NetworkHostList(q.all())
        else:
            return SimpleNetworkList(q.all())
