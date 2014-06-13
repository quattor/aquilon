# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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

import os

from aquilon.exceptions_ import (AuthorizationException, ArgumentError,
                                 ProcessException)
from aquilon.aqdb.model import Sandbox, Branch
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.get import CommandGet
from aquilon.worker.dbwrappers.branch import force_my_sandbox
from aquilon.worker.processes import run_git
from aquilon.utils import validate_template_name


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

        sandbox, dbauthor = force_my_sandbox(session, dbuser, sandbox)

        # See `git check-ref-format --help` for naming restrictions.
        # We want to layer a few extra restrictions on top of that...
        validate_template_name("--sandbox", sandbox)
        try:
            run_git(["check-ref-format", "--branch", sandbox])
        except ProcessException:
            raise ArgumentError("'%s' is not a valid git branch name." % sandbox)

        Branch.get_unique(session, sandbox, preclude=True)

        # Check that the user has cleared up a directory of the same
        # name; if this is not the case the branch may be created (in git)
        # and added to the database - however CommandGet will fail roleing
        # back the database leaving the branch created in git
        templatesdir = self.config.get("broker", "templatesdir")
        sandboxdir = os.path.join(templatesdir, dbauthor.name, sandbox)
        if os.path.exists(sandboxdir):
            raise ArgumentError("Sandbox directory %s already exists; "
                                "cannot create branch." %
                                sandboxdir)

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

        # If we arrive there the above "git branch" command has succeeded;
        # therefore we should comit the changes to the database.  If this is
        # not done, and CommandGet fails (see dir check above), then the
        # git branch will be created but the database changes roled back.
        session.commit()

        if get is False:
            # The client knows to interpret an empty response as no action.
            return []

        return CommandGet.render(self, session=session, logger=logger,
                                 dbuser=dbuser, sandbox=sandbox)
