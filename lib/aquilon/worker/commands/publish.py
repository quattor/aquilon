# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq publish`."""

import os
import re
from tempfile import mkstemp, mkdtemp
from base64 import b64decode

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Sandbox
from aquilon.worker.processes import run_git, sync_domain
from aquilon.worker.logger import CLIENT_INFO
from aquilon.utils import write_file, remove_file, remove_dir


class CommandPublish(BrokerCommand):

    required_parameters = ["bundle"]

    def render(self, session, logger, branch, sandbox, bundle, sync, rebase,
               **arguments):
        # Most of the logic here is duplicated in deploy
        if branch:
            sandbox = branch
        dbsandbox = Sandbox.get_unique(session, sandbox, compel=True)

        (handle, filename) = mkstemp()
        contents = b64decode(bundle)
        write_file(filename, contents, logger=logger)

        if sync and not dbsandbox.is_sync_valid and dbsandbox.trackers:
            # FIXME: Maybe raise an ArgumentError and request that the
            # command run with --nosync?  Maybe provide a --validate flag?
            # For now, we just auto-flip anyway (below) making the point moot.
            pass
        if not dbsandbox.is_sync_valid:
            dbsandbox.is_sync_valid = True

        if rebase and dbsandbox.trackers:
            raise ArgumentError("{0} has trackers, rebasing is not allowed."
                                .format(dbsandbox))

        kingdir = self.config.get("broker", "kingdir")
        rundir = self.config.get("broker", "rundir")

        tempdir = mkdtemp(prefix="publish_", suffix="_%s" % dbsandbox.name,
                          dir=rundir)
        try:
            run_git(["clone", "--shared", "--branch", dbsandbox.name,
                     kingdir, dbsandbox.name],
                    path=tempdir, logger=logger)
            temprepo = os.path.join(tempdir, dbsandbox.name)
            run_git(["bundle", "verify", filename],
                    path=temprepo, logger=logger)
            ref = "HEAD:%s" % (dbsandbox.name)
            command = ["pull", filename, ref]
            if rebase:
                command.append("--force")
            run_git(command, path=temprepo, logger=logger, loglevel=CLIENT_INFO)

            # Using --force above allows rewriting any history, even before the
            # start of the sandbox. We don't want to allow that, so verify that
            # the starting point of the sandbox is still part of its history.
            if rebase:
                filterre = re.compile('^' + dbsandbox.base_commit + '$')
                try:
                    found = run_git(['rev-list', dbsandbox.name],
                                    filterre=filterre, path=temprepo,
                                    logger=logger)
                except ProcessException, pe:
                    if pe.code != 128:
                        raise
                    else:
                        found = False

                if not found:
                    raise ArgumentError("The published branch no longer "
                                        "contains commit %s it was branched "
                                        "from." % dbsandbox.base_commit)

            # FIXME: Run tests before pushing back to template-king
            if rebase:
                target_ref = "+" + dbsandbox.name
            else:
                target_ref = dbsandbox.name
            run_git(["push", "origin", target_ref],
                    path=temprepo, logger=logger)
        except ProcessException, e:
            raise ArgumentError("\n%s%s" % (e.out, e.err))
        finally:
            remove_file(filename, logger=logger)
            remove_dir(tempdir, logger=logger)

        client_command = "git fetch"
        if not sync or not dbsandbox.autosync:
            return client_command

        for domain in dbsandbox.trackers:
            if not domain.autosync:
                continue
            try:
                sync_domain(domain, logger=logger)
            except ProcessException, e:
                logger.warn("Error syncing domain %s: %s" % (domain.name, e))

        return client_command
