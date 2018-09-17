# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq deploy`."""

import re

from aquilon.exceptions_ import (
    ProcessException,
    ArgumentError
)
from aquilon.aqdb.model import (
    Branch,
    Domain,
    Review,
    Sandbox
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import (
    sync_domain,
    sync_all_trackers,
    trigger_review_domain_update
)
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.processes import GitRepo
from aquilon.worker.logger import CLIENT_INFO

# Merge strategies and strategy option regexes we accept. The list
# intentionally contains just a small subset of what git can do.
_git_strategies = {
    "resolve": None,
    "recursive": re.compile("^(no-renames)$"),
}


class CommandDeploy(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, logger, source, target, sync, dryrun,
               merge_strategy, strategy_options, justification, reason, user,
               requestid, **arguments):
        # Most of the logic here is duplicated in publish
        dbsource = Branch.get_unique(session, source, compel=True)

        # The target has to be a non-tracking domain
        dbtarget = Domain.get_unique(session, target, compel=True)

        if sync and isinstance(dbtarget.tracked_branch, Domain) \
           and dbtarget.tracked_branch.autosync and dbtarget.autosync:
            # The user probably meant to deploy to the tracked branch,
            # but only do so if all the relevant autosync flags are
            # positive.
            logger.warning("Deploying to tracked branch %s and then will "
                           "auto-sync %s" % (dbtarget.tracked_branch.name,
                                             dbtarget.name))
            dbtarget = dbtarget.tracked_branch
        elif dbtarget.tracked_branch:
            raise ArgumentError("Cannot deploy to tracking domain %s.  "
                                "Did you mean domain %s?" %
                                (dbtarget.name, dbtarget.tracked_branch.name))

        if sync and not dbtarget.is_sync_valid and dbtarget.trackers:
            raise ArgumentError("{0} has not been validated, automatic sync "
                                "is not allowed. Either re-ryn with --nosync "
                                "or validate the branch.".format(dbtarget))

        dbreview = Review.get_unique(session, source=dbsource, target=dbtarget)
        if dbreview and dbreview.approved is False:
            raise ArgumentError("Deploying {0:l} to {1:l} "
                                "was explicitly denied."
                                .format(dbsource, dbtarget))

        if not dryrun:
            # Validate ChangeManagement
            arguments['requestid'] = requestid
            cm = ChangeManagement(session, user, justification, reason,
                                  logger, self.command, **arguments)
            cm.consider(dbtarget)
            cm.validate()

        # if not dbreview or not dbreview.approved:
            # logger.warning("Warning: this deployment request was not "
            #                "approved, this will be an error in the future.")

        if dbtarget.archived:
            raise ArgumentError("{0} is archived and cannot be changed."
                                .format(dbtarget))

        if isinstance(dbsource, Sandbox):
            repo = GitRepo.domain(dbtarget.name, logger)
            found = repo.ref_contains_commit(dbsource.base_commit)
            if not found:
                raise ArgumentError("You're trying to deploy a sandbox to a "
                                    "domain that does not contain the commit "
                                    "where the sandbox was branched from.")

        update_review_pipeline = False

        merge_args = []
        if merge_strategy:
            if merge_strategy not in _git_strategies:
                raise ArgumentError("Unknown or unsupported merge strategy.")
            merge_args.extend(["-s", merge_strategy])
            if strategy_options:
                if not _git_strategies[merge_strategy] or \
                        not _git_strategies[merge_strategy].search(
                            strategy_options):
                    raise ArgumentError("Unknown or unsupported "
                                        "strategy options.")
                merge_args.extend(["-X", strategy_options])

        kingrepo = GitRepo(self.config.get("broker", "kingdir"), logger)
        with kingrepo.temp_clone(dbtarget.name) as temprepo:
            # We could try to use fmt-merge-msg but its usage is so obscure
            # that faking it is easier
            merge_msg = []
            merge_msg.append("Merge remote branch 'origin/%s' into %s" %
                             (dbsource.name, dbtarget.name))
            merge_msg.append("")

            # TODO: The rest tries to look RFC2822-parseable,
            # but e.g. a newline
            # in --reason may cause surprises.
            merge_msg.append("User: %s" % user)
            merge_msg.append("Request-ID: %s" % requestid)
            if justification:
                merge_msg.append("Justification: %s" % justification)
            if reason:
                merge_msg.append("Reason: %s" % reason)

            if dbreview:
                if dbreview.review_url:
                    merge_msg.append("Code-Review-URL: %s" %
                                     dbreview.review_url)
                if dbreview.testing_url:
                    merge_msg.append("Testing-URL: %s" % dbreview.testing_url)

            try:
                cmd = ["merge", "--no-ff", "origin/%s" % dbsource.name,
                       "-m", "\n".join(merge_msg)]
                if merge_args:
                    cmd.extend(merge_args)

                temprepo.run(cmd, stream_level=CLIENT_INFO)

                update_review_pipeline = True
            except ProcessException as e:
                # No need to re-print e, output should have gone to client
                # immediately via the logger.
                raise ArgumentError("Failed to merge changes from %s into %s" %
                                    (dbsource.name, dbtarget.name))
            # FIXME: Run tests before pushing back to template-king.
            # Use a different try/except and a specific error message.

            if dryrun:
                session.rollback()
                return

            temprepo.push_origin(dbtarget.name)

        if update_review_pipeline:
            trigger_review_domain_update(target=dbtarget.name, logger=logger)

        # What to do about errors here and below... rolling back
        # doesn't seem appropriate as there's something more
        # fundamentally wrong with the repos.
        try:
            sync_domain(dbtarget, logger=logger)
        except ProcessException as e:
            logger.warning("Error syncing domain %s: %s" % (dbtarget.name, e))

        if sync and dbtarget.autosync:
            sync_all_trackers(dbtarget, logger)

        # TODO: if there are other unmerged changes under review, then trigger
        # new tests. Note that we cannot roll back the DB transaction at this
        # point, so the triggering the tests cannot fail. We may need an
        # explict session.commit() here.

        return
