#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del cpu`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.aqdb.hw.cpu import Cpu


class CommandDelCpu(BrokerCommand):

    required_parameters = ["cpu", "vendor", "speed"]

    @add_transaction
    @az_check
    def render(self, session, cpu, vendor, speed, **arguments):
        dbvendor = get_vendor(session, vendor)
        speed = force_int("speed", speed)
        try:
            dbcpu = session.query(Cpu).filter_by(name=cpu, vendor=dbvendor,
                    speed=speed).one()
        except:
            raise NotFoundException("Cpu %s not found: %s" % (cpu, e))
        try:
            session.delete(dbcpu)
        except InvalidRequestError, e:
            raise ArgumentError("Could not del cpu: %s" % e)
        return


#if __name__=='__main__':
