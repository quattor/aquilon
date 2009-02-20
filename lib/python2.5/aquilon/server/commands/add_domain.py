# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add domain`."""


import os

from aquilon.exceptions_ import (AuthorizationException, ArgumentError)
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.sy.domain import Domain
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)
from aquilon.server.dbwrappers.quattor_server import (
        get_or_create_quattor_server)
from aquilon.server.processes import run_command
import re

class CommandAddDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, domain, user, **arguments):
        dbuser = get_or_create_user_principal(session, user)
        if not dbuser:
            raise AuthorizationException("Cannot create a domain without"
                    + " an authenticated connection.")
        dbquattor_server = get_or_create_quattor_server(session,
                self.config.get("broker", "servername"))

        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(domain)):
            raise ArgumentError("domain name '%s' is not valid"%domain)

        # For now, succeed without error if the domain already exists.
        dbdomain = session.query(Domain).filter_by(name=domain).first()
        if not dbdomain:
            compiler = self.config.get("broker", "domain_default_panc")
            dbdomain = Domain(name=domain, server=dbquattor_server,
                              owner=dbuser, compiler=compiler)
            session.add(dbdomain)
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        # FIXME: If this command fails, should the domain entry be
        # created in the database anyway?
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
            os.environ.get("PATH", ""))}
        run_command(["git", "clone", self.config.get("broker", "kingdir"),
            domaindir], env=git_env)
        # The 1.0 code notes that this should probably be done as a
        # hook in git... just need to make sure it runs.
        run_command(["git-update-server-info"], env=git_env, path=domaindir)
        return


