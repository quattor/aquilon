# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013  Contributor
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
"""Contains the logic for `aq rollback`."""


import os
import re

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Domain
from aquilon.worker.processes import run_git
from aquilon.worker.locks import CompileKey


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
        dbdomain.rollback_commit = None

        with CompileKey(domain=dbdomain.name, logger=logger):
            try:
                run_git(["push", ".", "+%s:%s" % (ref, dbdomain.name)],
                        path=kingdir, logger=logger)
                # Duplicated this logic from aquilon.worker.processes.sync_domain()
                run_git(["fetch"], path=domaindir, logger=logger)
                run_git(["reset", "--hard", "origin/%s" % dbdomain.name],
                        path=domaindir, logger=logger)
            except ProcessException, e:
                raise ArgumentError("Problem encountered updating templates "
                                    "for domain %s: %s", dbdomain.name, e)

        return
