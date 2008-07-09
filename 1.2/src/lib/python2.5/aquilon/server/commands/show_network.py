#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show network`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.network import Network
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.server.formats.network import SimpleNetworkList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    @add_transaction
    @az_check
    @format_results
    def render(self, session, network, ip, type, **arguments):
        dbnetwork = network and get_network_byname(session, network) or None
        dbip = ip and get_network_byip(session, ip) or None
        q = session.query(Network)
        if dbnetwork:
            return dbnetwork
        if dbip:
            return dbip
        if type:
            q = q.join('type').filter_by(type=type)
            q = q.reset_joinpoint()
        dblocation = get_location(session, **arguments)
        if dblocation:
            q = q.filter_by(location=dblocation)
        return SimpleNetworkList(q.all())


#if __name__=='__main__':
