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
"""Contains the logic for `aq deploy`."""


import os
from tempfile import mkdtemp

from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Domain, Branch
from aquilon.server.broker import BrokerCommand
from aquilon.server.processes import run_git, remove_dir, sync_domain
from aquilon.server.logger import CLIENT_INFO


class CommandDeploy(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, logger, source, target, sync, dryrun,
               comments, user, requestid, **arguments):
        # Most of the logic here is duplicated in publish
        dbsource = Branch.get_unique(session, source, compel=True)

        # The target has to be a non-tracking domain
        dbtarget = Domain.get_unique(session, target, compel=True)

        if sync and dbtarget.tracked_branch \
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
