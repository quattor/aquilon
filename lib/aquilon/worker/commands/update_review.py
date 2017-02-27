# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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

import re

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Branch, Domain, Review
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import GitRepo

# Require full commit IDs to be passed, so we don't have to worry about
# collisions
_commit_re = re.compile("^[0-9a-fA-F]{40}$")


class CommandUpdateReview(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, logger, source, target, commit_id,
               testing_succeeded, testing_url, target_commit_tested, review_url,
               approved, **_):
        dbsource = Branch.get_unique(session, source, compel=True)
        dbtarget = Domain.get_unique(session, target, compel=True)

        dbreview = Review.get_unique(session, source=dbsource, target=dbtarget,
                                     compel=True)

        # Automated tools are expected to pass --commit_id, in case the review
        # was updated in the mean time
        if commit_id:
            if not _commit_re.search(commit_id):
                raise ArgumentError("Invalid commit ID (%s), make sure to pass "
                                    "the full hash." % commit_id)

            if dbreview.commit_id.lower() != commit_id.lower():
                raise ArgumentError("Possible attempt to update an old review "
                                    "record - the commit being reviewed is %s, "
                                    "not %s."
                                    % (dbreview.commit_id, commit_id))

        if testing_succeeded is not None:
            dbreview.tested = testing_succeeded

        if target_commit_tested:
            if not _commit_re.search(target_commit_tested):
                raise ArgumentError("Invalid commit ID (%s), make sure to pass "
                                    "the full hash." % target_commit_tested)
            repo = GitRepo.domain(dbtarget.name, logger)
            if not repo.ref_contains_commit(target_commit_tested,
                                            ref=dbtarget.name):
                raise ArgumentError("{0} does not contain commit {1!s}."
                                    .format(dbtarget, target_commit_tested))
            dbreview.target_commit_id = target_commit_tested.lower()

        if testing_url is not None:
            dbreview.testing_url = testing_url

        if review_url is not None:
            dbreview.review_url = review_url

        if approved is not None:
            dbreview.approved = approved

        session.flush()

        return
