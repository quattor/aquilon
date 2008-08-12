#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq status`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)


class CommandStatus(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, user, **arguments):
        stat = []
        # FIXME: Hard coded version number.
        stat.append("Aquilon Broker v1.2.1")
        stat.append("Server: %s" % self.config.get("broker", "servername"))
        stat.append("Database: %s" % self.config.get("database", "dsn"))
        dbuser = get_or_create_user_principal(session, user)
        if dbuser:
            stat.append("Connected as: %s [%s]" % (dbuser, dbuser.role.name))
        return stat

#if __name__=='__main__':
