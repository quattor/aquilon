#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show chassis`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.sy.chassis import Chassis


class CommandShowChassis(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        return session.query(Chassis).all()


#if __name__=='__main__':
