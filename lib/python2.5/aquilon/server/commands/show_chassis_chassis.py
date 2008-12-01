# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show chassis --chassis`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.sy.chassis import Chassis


class CommandShowChassisChassis(BrokerCommand):

    required_parameters = ["chassis"]

    def render(self, session, chassis, **arguments):
        return get_system(session, chassis, Chassis, 'Chassis')


