# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq permission`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)
from aquilon.server.dbwrappers.role import get_role


class CommandPermission(BrokerCommand):

    required_parameters = ["principal", "role"]

    def render(self, session, principal, role, createuser, createrealm,
            **arguments):
        dbrole = get_role(session, role)
        dbuser = get_or_create_user_principal(session, principal, 
                createuser, createrealm)
        dbuser.role = dbrole
        session.add(dbuser)
        return


