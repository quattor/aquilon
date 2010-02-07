# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add sandbox`."""


import re

from aquilon.exceptions_ import (AuthorizationException, ArgumentError)
from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.get import CommandGet
from aquilon.aqdb.model import Sandbox, Branch
from aquilon.server.processes import run_git


class CommandAddSandbox(CommandGet):

    required_parameters = ["sandbox"]
    # Need to override CommandGet which has this as True...
    requires_readonly = False

    def render(self, session, logger, dbuser, sandbox, start, noget, comments,
               **arguments):
        if not dbuser:
            raise AuthorizationException("Cannot create a sandbox without an "
                                         "authenticated connection.")

        sandbox = self.force_my_sandbox(session, logger, dbuser, sandbox)

        # See `git check-ref-format --help` for naming restrictions.
        # We want to layer a few extra restrictions on top of that...
        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(sandbox)):
            raise ArgumentError("sandbox name '%s' is not valid" % sandbox)

        Branch.get_unique(session, sandbox, preclude=True)

        if not start:
            start = self.config.get("broker", "default_domain_start")
        dbstart = Branch.get_unique(session, start, compel=True)

        compiler = self.config.get("panc", "pan_compiler")
        dbsandbox = Sandbox(name=sandbox, owner=dbuser, compiler=compiler,
                            comments=comments)
        session.add(dbsandbox)
        session.flush()
        session.refresh(dbsandbox)
        # Get the cleaned up version...
        sandbox = dbsandbox.name

        # Currently this will fail if the branch already exists...
        # That seems like the right behavior.  It's an internal
        # consistency issue that would need to be addressed explicitly.
        run_git(["branch", sandbox, dbstart.name],
                logger=logger, path=self.config.get("broker", "kingdir"))

        if noget:
            # The client will try to execute an empty string here, which
            # is harmless.
            return

        return CommandGet.render(self, session=session, logger=logger,
                                 dbuser=dbuser, sandbox=sandbox)
