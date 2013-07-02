# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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


import os
import re
from tempfile import mkdtemp

from aquilon.exceptions_ import (ProcessException, ArgumentError,
                                 AuthorizationException)
from aquilon.aqdb.model import Domain, Branch, Sandbox
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import run_git, sync_domain
from aquilon.worker.logger import CLIENT_INFO
from aquilon.utils import remove_dir

TCM_RE = re.compile(r"^tcm=([0-9]+)$", re.IGNORECASE)
SN_RE = re.compile(r"^sn=([a-z]+[0-9]+)$", re.IGNORECASE)


# TODO: move this to an external class
def validate_justification(principal, justification):
    result = None
    for valid_re in [TCM_RE, SN_RE]:
        result = valid_re.search(justification)
        if result:
            break
    if not result:
        raise ArgumentError("Failed to parse the justification: expected "
                            "tcm=NNNNNNNNN or sn=XXXNNNNN.")
    # TODO: EDM validation
    #edm_validate(result.group(0))


class CommandDeploy(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, logger, source, target, sync, dryrun,
               comments, justification, user, requestid, **arguments):
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
                           "auto-sync %s" % (
                           dbtarget.tracked_branch.name, dbtarget.name))
            dbtarget = dbtarget.tracked_branch
        elif dbtarget.tracked_branch:
            raise ArgumentError("Cannot deploy to tracking domain %s.  "
                                "Did you mean domain %s?" %
                                (dbtarget.name, dbtarget.tracked_branch.name))

        if sync and not dbtarget.is_sync_valid and dbtarget.trackers:
            # FIXME: Maybe raise an ArgumentError and request that the
            # command run with --nosync?  Maybe provide a --validate flag?
            # For now, just auto-flip (below).
            pass
        if not dbtarget.is_sync_valid:
            dbtarget.is_sync_valid = True

        if dbtarget.requires_change_manager:
            if not justification:
                raise AuthorizationException(
                    "{0} is under change management control.  Please specify "
                    "--justification.".format(dbtarget))
            validate_justification(user, justification)

        if isinstance(dbsource, Sandbox):
            domainsdir = self.config.get('broker', 'domainsdir')
            targetdir = os.path.join(domainsdir, dbtarget.name)
            filterre = re.compile('^' + dbsource.base_commit + '$')
            found = run_git(['rev-list', 'HEAD'], path=targetdir,
                            logger=logger, filterre=filterre)
            if not found:
                raise ArgumentError("You're trying to deploy a sandbox to a "
                                    "domain that does not contain the commit "
                                    "where the sandbox was branched from.")

        kingdir = self.config.get("broker", "kingdir")
        rundir = self.config.get("broker", "rundir")

        tempdir = mkdtemp(prefix="deploy_", suffix="_%s" % dbsource.name,
                          dir=rundir)
        try:
            run_git(["clone", "--shared", "--branch", dbtarget.name,
                     kingdir, dbtarget.name],
                    path=tempdir, logger=logger)
            temprepo = os.path.join(tempdir, dbtarget.name)

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
            if comments:
                merge_msg.append("Comments: %s" % comments)

            try:
                run_git(["merge", "--no-ff", "origin/%s" % dbsource.name,
                         "-m", "\n".join(merge_msg)],
                        path=temprepo, logger=logger, loglevel=CLIENT_INFO)
            except ProcessException, e:
                # No need to re-print e, output should have gone to client
                # immediately via the logger.
                raise ArgumentError("Failed to merge changes from %s into %s" %
                                    (dbsource.name, dbtarget.name))
            # FIXME: Run tests before pushing back to template-king.
            # Use a different try/except and a specific error message.

            if dryrun:
                session.rollback()
                return

            run_git(["push", "origin", dbtarget.name],
                    path=temprepo, logger=logger)
        finally:
            remove_dir(tempdir, logger=logger)

        # What to do about errors here and below... rolling back
        # doesn't seem appropriate as there's something more
        # fundamentally wrong with the repos.
        try:
            sync_domain(dbtarget, logger=logger)
        except ProcessException, e:
            logger.warn("Error syncing domain %s: %s" % (dbtarget.name, e))

        if not sync or not dbtarget.autosync:
            return

        for domain in dbtarget.trackers:
            if not domain.autosync:
                continue
            try:
                sync_domain(domain, logger=logger)
            except ProcessException, e:
                logger.warn("Error syncing domain %s: %s" % (domain.name, e))

        return
