# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add cpu`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.aqdb.hw.cpu import Cpu


class CommandAddCpu(BrokerCommand):

    required_parameters = ["cpu", "vendor", "speed"]

    @add_transaction
    @az_check
    def render(self, session, cpu, vendor, speed, comments, **arguments):
        dbvendor = get_vendor(session, vendor)
        speed = force_int("speed", speed)
        dbcpu = Cpu(name=cpu, vendor=dbvendor, speed=speed, comments=comments)
        try:
            session.save(dbcpu)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add cpu: %s" % e)
        return


