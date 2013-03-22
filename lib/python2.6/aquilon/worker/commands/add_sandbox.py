# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq add sandbox`."""


import re

from aquilon.exceptions_ import (AuthorizationException, ArgumentError)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.get import CommandGet
from aquilon.aqdb.model import Sandbox, Branch
from aquilon.worker.processes import run_git


class CommandAddSandbox(CommandGet):

    required_parameters = ["sandbox"]
    # Need to override CommandGet which has this as True...
    requires_readonly = False
    default_style = "csv"
    requires_format = True

    def render(self, session, logger, dbuser, sandbox, start, get, comments,
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

        kingdir = self.config.get("broker", "kingdir")
        base_commit = run_git(["show-ref", "--hash", "refs/heads/" +
                               dbstart.name], logger=logger, path=kingdir)

        compiler = self.config.get("panc", "pan_compiler")
        dbsandbox = Sandbox(name=sandbox, owner=dbuser, compiler=compiler,
                            base_commit=base_commit, comments=comments)
        session.add(dbsandbox)
        session.flush()

        # Currently this will fail if the branch already exists...
        # That seems like the right behavior.  It's an internal
        # consistency issue that would need to be addressed explicitly.
        run_git(["branch", sandbox, dbstart.name], logger=logger, path=kingdir)

        if get == False:
            # The client knows to interpret an empty response as no action.
            return []

        return CommandGet.render(self, session=session, logger=logger,
                                 dbuser=dbuser, sandbox=sandbox)
