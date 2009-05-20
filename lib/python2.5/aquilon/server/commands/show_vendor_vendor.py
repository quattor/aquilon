# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying
#
# This module is part of Aquilon


from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hw import Vendor
from aquilon.server.broker import BrokerCommand


class CommandShowVendorVendor(BrokerCommand):

    required_parameters = [ "vendor" ]

    def render(self, session, vendor, **arguments):
        dbvendor = session.query(Vendor).filter_by(name=vendor).first()
        if not dbvendor:
            raise NotFoundException("Could not find vendor with name '%s'." %
                                    vendor)
        return dbvendor


