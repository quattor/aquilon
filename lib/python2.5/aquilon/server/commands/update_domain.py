# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update domain`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)
from aquilon.server.dbwrappers.domain import get_domain


class CommandUpdateDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, domain, comments, owner, compiler, user,
               **arguments):
        dbdomain = get_domain(session, domain)
        if owner:
            dbowner = get_or_create_user_principal(session, owner,
                                                   createuser=False,
                                                   createrealm=False)
            dbdomain.owner = dbowner
        if comments:
            dbdomain.comments = comments
        if compiler:
            dbdomain.compiler = compiler
        session.add(dbdomain)
        return


