# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from aquilon.exceptions_ import (ProcessException, ArgumentError,
                                 AuthorizationException)
from aquilon.aqdb.model import Domain, Branch, Sandbox
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import sync_domain, sync_all_trackers
from aquilon.worker.dbwrappers.change_management import validate_justification
from aquilon.worker.processes import GitRepo
from aquilon.worker.logger import CLIENT_INFO


class CommandDeploy(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, logger, source, target, sync, dryrun,
               justification, reason, user, requestid, **_):
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

        if dbtarget.requires_change_manager and not dryrun:
            if not justification:
                raise AuthorizationException(
                    "{0} is under change management control.  Please specify "
                    "--justification.".format(dbtarget))
            validate_justification(user, justification, reason)

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

        kingrepo = GitRepo(self.config.get("broker", "kingdir"), logger)
        with kingrepo.temp_clone(dbtarget.name) as temprepo:
            # We could try to use fmt-merge-msg but its usage is so obscure that
            # faking it is easier
            merge_msg = []
            merge_msg.append("Merge remote branch 'origin/%s' into %s" %
                             (dbsource.name, dbtarget.name))
            merge_msg.append("")
            merge_msg.append("User: %s" % user)
            merge_msg.append("Request ID: %s" % requestid)
            if justification:
                merge_msg.append("Justification: %s" % justification)
            if reason:
                merge_msg.append("Reason: %s" % reason)

            try:
                temprepo.run(["merge", "--no-ff", "origin/%s" % dbsource.name,
                              "-m", "\n".join(merge_msg)],
                             stream_level=CLIENT_INFO)
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

        # What to do about errors here and below... rolling back
        # doesn't seem appropriate as there's something more
        # fundamentally wrong with the repos.
        try:
            sync_domain(dbtarget, logger=logger)
        except ProcessException as e:
            logger.warning("Error syncing domain %s: %s" % (dbtarget.name, e))

        if sync and dbtarget.autosync:
            sync_all_trackers(dbtarget, logger)

        return
