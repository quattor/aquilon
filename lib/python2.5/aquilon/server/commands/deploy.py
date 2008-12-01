# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq deploy`."""


import os

from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.processes import run_command


class CommandDeploy(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, domain, to, **arguments):
        """ This currently ignores the 'to' parameter."""

        # Verify that it exists before trying to deploy it.
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
                os.environ.get("PATH", ""))}
        run_command(["git", "pull", domaindir], env=git_env,
                path=self.config.get("broker", "kingdir"))
        return


