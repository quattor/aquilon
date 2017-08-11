# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013,2014,2016,2017  Contributor
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

from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Domain
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import GitRepo
from aquilon.worker.locks import CompileKey
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandRollback(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, domain, ref, lastsync, user,
               justification, reason, **_):
        dbdomain = Domain.get_unique(session, domain, compel=True)
        if not dbdomain.tracked_branch:
            # Could check dbdomain.trackers and rollback all of them...
            raise ArgumentError("Rollback requires a tracking domain.")

        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbdomain)
        cm.validate()

        kingrepo = GitRepo.template_king(logger)
        domainrepo = GitRepo.domain(dbdomain.name, logger)

        if lastsync:
            if not dbdomain.rollback_commit:
                raise ArgumentError("{0} does not have a rollback "
                                    "commit saved, please specify one "
                                    "explicitly.".format(dbdomain))
            commit_id = dbdomain.rollback_commit
        else:
            commit_id = kingrepo.ref_commit(ref)

        if not commit_id:
            raise ArgumentError("Commit reference to rollback to required.")

        if not kingrepo.ref_contains_commit(commit_id,
                                            dbdomain.tracked_branch.name):
            # There's no real technical reason why this needs to be
            # true.  It just seems like a good sanity check.
            raise ArgumentError("Cannot roll back to commit: "
                                "branch %s does not contain %s" %
                                (dbdomain.tracked_branch.name, commit_id))

        dbdomain.tracked_branch.is_sync_valid = False
        dbdomain.rollback_commit = None

        with CompileKey(domain=dbdomain.name, logger=logger):
            try:
                kingrepo.run(["push", ".", "+%s:%s" % (commit_id, dbdomain.name)])
                # Duplicated this logic from aquilon.worker.dbwrappers.branch.sync_domain()
                domainrepo.run(["fetch"])
                domainrepo.run(["reset", "--hard", "origin/%s" % dbdomain.name])
            except ProcessException as e:
                raise ArgumentError("Problem encountered updating templates "
                                    "for domain %s: %s", dbdomain.name, e)

        return
