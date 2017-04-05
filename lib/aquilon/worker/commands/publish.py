# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from tempfile import NamedTemporaryFile
from base64 import b64decode

from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Sandbox
from aquilon.worker.dbwrappers.branch import force_my_sandbox, sync_all_trackers
from aquilon.worker.processes import GitRepo
from aquilon.worker.logger import CLIENT_INFO


class CommandPublish(BrokerCommand):

    required_parameters = ["bundle"]
    requires_format = True

    def render(self, session, logger, dbuser, branch, sandbox, bundle, sync,
               rebase, **_):
        if sandbox:
            sandbox, _ = force_my_sandbox(session, dbuser, sandbox)
            dbsandbox = Sandbox.get_unique(session, sandbox, compel=True)
        elif branch:
            dbsandbox = Sandbox.get_unique(session, branch, compel=True)

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

        # Most of the logic here is duplicated in deploy
        kingdir = self.config.get("broker", "kingdir")

        tmpfile = NamedTemporaryFile()
        tmpfile.write(b64decode(bundle))
        tmpfile.flush()

        kingrepo = GitRepo(kingdir, logger)
        try:
            with kingrepo.temp_clone(dbsandbox.name) as temprepo:
                temprepo.run(["bundle", "verify", tmpfile.name])
                ref = "HEAD:%s" % (dbsandbox.name)
                command = ["pull", tmpfile.name, ref]
                if rebase:
                    command.append("--force")
                temprepo.run(command, stream_level=CLIENT_INFO)

                # Using --force above allows rewriting any history, even before the
                # start of the sandbox. We don't want to allow that, so verify that
                # the starting point of the sandbox is still part of its history.
                if rebase:
                    found = temprepo.ref_contains_commit(dbsandbox.base_commit,
                                                         dbsandbox.name)
                    if not found:
                        raise ArgumentError("The published branch no longer "
                                            "contains commit %s it was branched "
                                            "from." % dbsandbox.base_commit)

                # FIXME: Run tests before pushing back to template-king
                temprepo.push_origin(dbsandbox.name, force=rebase)
        except ProcessException as e:
            raise ArgumentError("\n%s%s" % (e.out, e.err))
        finally:
            tmpfile.close()

        if sync and dbsandbox.autosync:
            sync_all_trackers(dbsandbox, logger)

        # Invalidate previous reviews
        new_head = kingrepo.ref_commit(dbsandbox.name)
        for dbreview in dbsandbox.reviews:
            dbreview.commit_id = new_head
            dbreview.tested = None
            dbreview.testing_url = None

            # Explicit denials should be kept
            if dbreview.approved is True:
                dbreview.approved = None

        session.flush()

        client_command = "git fetch"
        return client_command
