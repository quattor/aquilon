# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying
#
# This module is part of Aquilon

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.hw import Vendor

class CommandShowVendorVendor(BrokerCommand):

    required_parameters = [ "vendor" ]

    def render(self, session, vendor, **arguments):
        vlist = session.query(Vendor).filter_by(name=vendor).all()
        return vlist


