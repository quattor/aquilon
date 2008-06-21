#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq manage`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.dbwrappers.host import hostname_to_host


class CommandManage(BrokerCommand):

    required_parameters = ["domain", "hostname"]

    @add_transaction
    @az_check
    def render(self, session, domain, hostname, **arguments):
        # FIXME: Need to verify that this server handles this domain?
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        dbhost = hostname_to_host(session, hostname)
        dbhost.domain = dbdomain
        session.save_or_update(dbhost)
        return


#if __name__=='__main__':
