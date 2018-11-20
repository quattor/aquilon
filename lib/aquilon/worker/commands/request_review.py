# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016-2018  Contributor
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

from aquilon.exceptions_ import ArgumentError

from aquilon.aqdb.model import (
    Branch,
    Domain,
    Review,
    Sandbox,
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import (
    force_my_sandbox,
    trigger_review_pipeline,
)
from aquilon.worker.processes import GitRepo

class CommandRequestReview(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, logger, dbuser, source, target, user, **_):
        source, _ = force_my_sandbox(session, dbuser, source)
        dbsandbox = Branch.get_unique(session, source, compel=True)
        dbtarget = Domain.get_unique(session, target, compel=True)

        if dbtarget.tracked_branch:
            if isinstance(dbtarget.tracked_branch, Sandbox):
                raise ArgumentError("{0} tracks a sandbox, changes should go "
                                    "through the sandbox.".format(dbtarget))
            raise ArgumentError("The target needs to be a non-tracking domain, "
                                "maybe you meant {0.name}?"
                                .format(dbtarget.tracked_branch))

        # "aq deploy" would check this, so let's catch errors early
        if isinstance(dbsandbox, Sandbox):
            repo = GitRepo.domain(dbtarget.name, logger)
            found = repo.ref_contains_commit(dbsandbox.base_commit)
            if not found:
                raise ArgumentError("{0} does not contain the commit where "
                                    "{1:l} was branched from."
                                    .format(dbtarget, dbsandbox))

        kingdir = self.config.get("broker", "kingdir")
        kingrepo = GitRepo(kingdir, logger)
        published_source_head = kingrepo.ref_commit(ref=dbsandbox.name)

        # try and find existing review
        dbreview = Review.get_unique(session,
                                     source=dbsandbox,
                                     target=dbtarget)

        if dbreview:
            # Invalidate previous review
            dbreview.commit_id = published_source_head
            dbreview.tested = None
            dbreview.testing_url = None

            # Explicit denials should be kept
            if dbreview.approved:
                dbreview.approved = None

        else:
            # Create new review
            dbreview = Review(source=dbsandbox,
                              target=dbtarget,
                              commit_id=published_source_head)
            session.add(dbreview)

        # Trigger CI Pipeline
        trigger_review_pipeline(dbreview=dbreview,
                                user=user,
                                logger=logger)

        session.add(dbreview)
        session.flush()

