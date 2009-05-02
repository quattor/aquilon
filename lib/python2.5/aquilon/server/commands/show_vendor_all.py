# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.hw import Vendor


class CommandShowVendorAll(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        vlist = session.query(Vendor).all()
        return vlist


