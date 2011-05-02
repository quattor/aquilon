# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Contains the logic for `aq rollback`."""


import os
import re

from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Domain
from aquilon.worker.processes import run_git
from aquilon.worker.locks import lock_queue, CompileKey


class CommandRollback(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, domain, ref, lastsync, **arguments):
        dbdomain = Domain.get_unique(session, domain, compel=True)
        if not dbdomain.tracked_branch:
            # Could check dbdomain.trackers and rollback all of them...
            raise ArgumentError("rollback requires a tracking domain")

        if lastsync:
            if not dbdomain.rollback_commit:
                raise ArgumentError("domain %s does not have a rollback "
                                    "commit saved, please specify one "
                                    "explicitly." % dbdomain.name)
            ref = dbdomain.rollback_commit

        if not ref:
            raise ArgumentError("Commit reference to rollback to required.")

        kingdir = self.config.get("broker", "kingdir")
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 dbdomain.name)
        out = run_git(["branch", "--contains", ref],
                      logger=logger, path=kingdir)
        if not re.search(r'\b%s\b' % dbdomain.tracked_branch.name, out):
            # There's no real technical reason why this needs to be
            # true.  It just seems like a good sanity check.
            raise ArgumentError("Cannot roll back to commit: "
                                "branch %s does not contain %s" %
                                (dbdomain.tracked_branch.name, ref))

        dbdomain.tracked_branch.is_sync_valid = False
        session.add(dbdomain.tracked_branch)
        dbdomain.rollback_commit = None
        session.add(dbdomain)

        key = CompileKey(domain=dbdomain.name, logger=logger)
        try:
            lock_queue.acquire(key)
            run_git(["push", ".", "+%s:%s" % (ref, dbdomain.name)],
                    path=kingdir, logger=logger)
            # Duplicated this logic from aquilon.worker.processes.sync_domain()
            run_git(["fetch"], path=domaindir, logger=logger)
            run_git(["reset", "--hard", "origin/%s" % dbdomain.name],
                    path=domaindir, logger=logger)
        except ProcessException, e:
            raise ArgumentError("Problem encountered updating templates for "
                                "domain %s: %s", dbdomain.name, e)
        finally:
            lock_queue.release(key)

        return
