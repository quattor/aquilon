# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq add sandbox`."""


import re

from aquilon.exceptions_ import (AuthorizationException, ArgumentError)
from aquilon.worker.broker import BrokerCommand
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
