#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del domain`."""


import os

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.processes import remove_dir


class CommandDelDomain(BrokerCommand):

    required_parameters = ["domain"]

    @add_transaction
    @az_check
    def render(self, session, domain, **arguments):
        # FIXME: This will fail if the domain does not exist.  We might
        # want to allow the directory to be deleted anyway, assuming it
        # is a valid domain name and az_check passes.
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        session.refresh(dbdomain)
        if dbdomain.hosts:
            raise ArgumentError("Cannot delete domain %s while hosts are still attached."
                    % dbdomain.name)
        session.delete(dbdomain)
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        remove_dir(domaindir)
        return


#if __name__=='__main__':
