# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show principal`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import UserPrincipal


class CommandShowPrincipal(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        return session.query(UserPrincipal).all()


