# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del domain`."""


import os

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.processes import remove_dir
from aquilon.server.templates.domain import TemplateDomain


class CommandDelDomain(BrokerCommand):

    required_parameters = ["domain"]

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

        domain = TemplateDomain(dbdomain)
        for dir in domain.directories():
            remove_dir(dir)

        return


