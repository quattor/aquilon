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

import os
import re

from aquilon.exceptions_ import (IncompleteError, ArgumentError,
                                 ProcessException)
from aquilon.aqdb.model import Sandbox
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.locks import CompileKey
from aquilon.worker.processes import run_git
from aquilon.worker.formats.branch import AuthoredSandbox
from aquilon.worker.templates import Plenary


def validate_branch_commits(dbsource, dbsource_author,
                            dbtarget, dbtarget_author, logger, config):
    domainsdir = config.get('broker', 'domainsdir')
    if isinstance(dbsource, Sandbox):
        authored_sandbox = AuthoredSandbox(dbsource, dbsource_author)
        source_path = authored_sandbox.path
    else:
        source_path = os.path.join(domainsdir, dbsource.name)

    if isinstance(dbtarget, Sandbox):
        authored_sandbox = AuthoredSandbox(dbtarget, dbtarget_author)
        target_path = authored_sandbox.path
    else:
        target_path = os.path.join(domainsdir, dbtarget.name)

    # check if dbsource has anything uncommitted
    git_status = run_git(["status", "--porcelain"],
                         path=source_path,
                         logger=logger)
    if git_status:
        raise ArgumentError("The source {0:l} contains uncommitted files."
                            .format(dbsource))

    # get latest source commit bit
    dbsource_commit = run_git(['rev-list', '--max-count=1', 'HEAD'],
                              path=source_path, logger=logger)
    dbsource_commit = dbsource_commit.rstrip()
    if not dbsource_commit:  # pragma: no cover
        raise ArgumentError("Unable to retrieve the git commit history from "
                            "source branch {0:l}.".format(dbsource))

    # make sure all commits in the source have been published.
    # we can check the latest commit bit from the source in template-king
    # any results returned will mean that all commits has been published
    kingdir = config.get("broker", "kingdir")
    try:
        found = run_git(['cat-file', '-t', dbsource_commit],
                        path=kingdir, logger=logger)
        found = found.strip()
    except ProcessException as pe:
        if pe.code != 128:
            raise
        else:
            found = None
    if found != 'commit':
        raise ArgumentError("The source {0:l} latest commit has not been "
                            "published to template-king yet.".format(dbsource))

    # check if target branch has the latest source commit
    try:
        filterre = re.compile('^' + dbsource_commit + '$')
        found = run_git(['rev-list', 'HEAD'], filterre=filterre,
                        path=target_path, logger=logger)
    except ProcessException as pe:
        if pe.code != 128:
            raise
        else:
            found = None
    if not found:
        raise ArgumentError("The target {0:l} does not contain the latest "
                            "commit from source {1:l}.".format(dbtarget,
                                                               dbsource))


class CommandManageHostname(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, domain, sandbox, force,
               **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing hosts to {0:l} is not allowed."
                                .format(dbbranch))

        dbhost = hostname_to_host(session, hostname)
        dbsource = dbhost.branch
        dbsource_author = dbhost.sandbox_author

        if dbhost.cluster:
            raise ArgumentError("Cluster nodes must be managed at the "
                                "cluster level; this host is a member of "
                                "{0}.".format(dbhost.cluster))

        if not force:
            validate_branch_commits(dbsource, dbsource_author,
                                    dbbranch, dbauthor, logger, self.config)

        plenary_host = Plenary.get_plenary(dbhost, logger=logger)

        dbhost.branch = dbbranch
        dbhost.sandbox_author = dbauthor

        session.flush()

        # We're crossing domains, need to lock everything.
        # XXX: There's a directory per domain.  Do we need subdirectories
        # for different authors for a sandbox?
        with CompileKey.merge([CompileKey(domain=dbsource.name, logger=logger),
                               CompileKey(domain=dbbranch.name, logger=logger)]):
            plenary_host.stash()
            try:
                plenary_host.write(locked=True)
            except IncompleteError:
                # This template cannot be written, we leave it alone
                # It would be nice to flag the state in the the host?
                plenary_host.remove(locked=True)
            except:
                # This will not restore the cleaned up build files.  That's OK.
                # They will be recreated as needed.
                plenary_host.restore_stash()
                raise

        return
