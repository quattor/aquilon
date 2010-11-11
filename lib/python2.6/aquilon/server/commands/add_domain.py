# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq add domain`."""


import os
import re

from aquilon.exceptions_ import (AuthorizationException, ArgumentError,
                                 InternalError, ProcessException)
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Domain, Branch
from aquilon.server.processes import run_git, remove_dir


class CommandAddDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, dbuser,
               domain, track, start, comments, **arguments):
        if not dbuser:
            raise AuthorizationException("Cannot create a domain without "
                                         "an authenticated connection.")

        Branch.get_unique(session, domain, preclude=True)

        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(domain)):
            raise ArgumentError("Domain name '%s' is not valid." % domain)

        # FIXME: Verify that track is a valid branch name?
        # Or just let the branch command fail?

        compiler = self.config.get("panc", "pan_compiler")
        dbtracked = None
        if track:
            dbtracked = Branch.get_unique(session, track, compel=True)
            if getattr(dbtracked, "tracked_branch", None):
                raise ArgumentError("Cannot nest tracking.  Try tracking "
                                    "{0:l} directly.".format(dbtracked.tracked_branch))
            start_point = dbtracked
        else:
            if not start:
                start = self.config.get("broker", "default_domain_start")
            start_point = Branch.get_unique(session, start, compel=True)

        dbdomain = Domain(name=domain, owner=dbuser, compiler=compiler,
                          tracked_branch=dbtracked, comments=comments)
        session.add(dbdomain)
        session.flush()

        domainsdir = self.config.get("broker", "domainsdir")
        clonedir = os.path.join(domainsdir, dbdomain.name)
        if os.path.exists(clonedir):
            raise InternalError("Domain directory already exists")

        kingdir = self.config.get("broker", "kingdir")
        cmd = ["branch"]
        if track:
            cmd.append("--track")
        else:
            cmd.append("--no-track")
        cmd.append(dbdomain.name)
        cmd.append(start_point.name)
        run_git(cmd, path=kingdir, logger=logger)

        # If the branch command above fails the DB will roll back as normal.
        # If the command below fails we need to clean up from itself and above.
        try:
            run_git(["clone", "--branch", dbdomain.name,
                     kingdir, dbdomain.name],
                    path=domainsdir, logger=logger)
        except ProcessException, e:
            try:
                remove_dir(clonedir, logger=logger)
                run_git(["branch", "-D", dbdomain.name],
                        path=kingdir, logger=logger)
            except ProcessException, e2:
                logger.info("Exception while cleaning up: %s", e2)
            raise e
        return
