# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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


import os

from aquilon.exceptions_ import IncompleteError, ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.processes import run_git
from aquilon.aqdb.model import Sandbox
from aquilon.worker.formats.branch import AuthoredSandbox
from aquilon.exceptions_ import ProcessException


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
                              path=source_path,
                              logger=logger)
    dbsource_commit = dbsource_commit.rstrip()
    if not dbsource_commit:  # pragma: no cover
        raise ArgumentError("Unable to retrieve the git commit history from "
                            "source branch {0:l}.".format(dbsource))

    # make sure all commits in the source have been published.
    # we can check the latest commit bit from the source in template-king
    # any results returned will mean that all commits has been published
    kingdir = config.get("broker", "kingdir")
    try:
        found = run_git(['show', dbsource_commit, '--oneline'],
                        path=kingdir, logger=logger)
    except ProcessException as pe:
        if pe.code != 128:
            raise
        else:
            found = None
    if not found:
        raise ArgumentError("The source {0:l} latest commit has not been "
                            "published to template-king yet.".format(dbsource))

    # check if target branch has the latest source commit
    try:
        found = run_git(['show', dbsource_commit, '--oneline'],
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
        old_branch = dbhost.branch.name

        if dbhost.cluster:
            raise ArgumentError("Cluster nodes must be managed at the "
                                "cluster level; this host is a member of "
                                "{0}.".format(dbhost.cluster))

        if not force:
            validate_branch_commits(dbsource, dbsource_author,
                                    dbbranch, dbauthor, logger, self.config)

        dbhost.branch = dbbranch
        dbhost.sandbox_author = dbauthor
        session.add(dbhost)
        session.flush()
        plenary_host = PlenaryHost(dbhost, logger=logger)

        # We're crossing domains, need to lock everything.
        # XXX: There's a directory per domain.  Do we need subdirectories
        # for different authors for a sandbox?
        key = CompileKey(logger=logger)

        try:
            lock_queue.acquire(key)

            plenary_host.stash()
            plenary_host.cleanup(old_branch, locked=True)

            # Now we recreate the plenary to ensure that the domain is ready
            # to compile, however (esp. if there was no existing template), we
            # have to be aware that there might not be enough information yet
            # with which we can create a template
            try:
                plenary_host.write(locked=True)
            except IncompleteError:
                # This template cannot be written, we leave it alone
                # It would be nice to flag the state in the the host?
                pass
        except:
            # This will not restore the cleaned up files.  That's OK.
            # They will be recreated as needed.
            plenary_host.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
