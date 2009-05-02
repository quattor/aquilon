# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information.
#
# This module is part of Aquilon

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.hw import Vendor
from aquilon.exceptions_ import ArgumentError
import re

class CommandAddVendor(BrokerCommand):

    required_parameters = [ "vendor" ]

    def render(self, session, vendor, **arguments):
        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(vendor)):
            raise ArgumentError("vendor name '%s' is not valid" % vendor)

        existing = session.query(Vendor).filter_by(name=vendor).first()
        if existing:
            raise ArgumentError("vendor '%s' already exists" % vendor)

        dbv = Vendor(name=vendor)
        session.save(dbv)
        return
