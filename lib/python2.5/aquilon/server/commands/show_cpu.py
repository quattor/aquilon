# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show cpu`."""


from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.aqdb.model import Cpu


class CommandShowCpu(BrokerCommand):

    def render(self, session, cpu, vendor, speed, **arguments):
        q = session.query(Cpu)
        if cpu:
            q = q.filter(Cpu.name.like(cpu + '%'))
        if vendor:
            dbvendor = get_vendor(session, vendor)
            q = q.filter_by(vendor=dbvendor)
        if speed:
            speed = force_int("speed", speed)
            q = q.filter_by(speed=speed)
        return q.all()


