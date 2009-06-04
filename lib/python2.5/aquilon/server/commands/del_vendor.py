# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information.
#
# This module is part of Aquilon


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Vendor, Cpu, Model
from aquilon.server.broker import BrokerCommand


class CommandDelVendor(BrokerCommand):

    required_parameters = [ "vendor" ]

    def render(self, session, vendor, **arguments):
        dbvendor = session.query(Vendor).filter_by(name=vendor).first()
        if not dbvendor:
            raise NotFoundException("No vendor with name '%s'" % vendor)
        if session.query(Model).filter_by(vendor=dbvendor).first():
            raise ArgumentError("Can not delete vendor '%s': "
                                "in use by a model." % dbvendor.name)
        if session.query(Cpu).filter_by(vendor=dbvendor).first():
            raise ArgumentError("Can not delete vendor '%s': "
                                "in use by a cpu." % dbvendor.name)
        session.delete(dbvendor)
        return


