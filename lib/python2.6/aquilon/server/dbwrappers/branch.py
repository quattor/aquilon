# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Wrapper to make getting a branch simpler."""


from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import Domain, Sandbox, Branch, UserPrincipal
from aquilon.server.dbwrappers.user_principal import get_user_principal
from aquilon.server.processes import remove_dir, run_git
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.server.templates.domain import TemplateDomain


def get_branch_and_author(session, logger,
                          domain=None, sandbox=None, branch=None,
                          compel=False):
    dbbranch = None
    dbauthor = None
    if domain:
        dbbranch = Domain.get_unique(session, domain, compel=True)
    elif branch:
        dbbranch = Branch.get_unique(session, branch, compel=True)
    elif sandbox:
        (author, slash, name) = sandbox.partition('/')
        if not slash:
            raise ArgumentError("Expected sandbox as 'author/branch', author "
                                "name and branch name separated by a slash.")
        dbbranch = Sandbox.get_unique(session, name, compel=True)
        dbauthor = get_user_principal(session, author)
    elif compel:
        raise ArgumentError("Please specify either sandbox or domain.")
    return (dbbranch, dbauthor)

def get_branch_dependencies(dbbranch):
    """Returns a list of strings describing how a branch is being used.

    If there are no dependencies then an empty list is returned.

    """
    ret = []
    if dbbranch.hosts:
        ret.append("Hosts are still attached to %s %s." %
                   (dbbranch.branch_type, dbbranch.name))
    if dbbranch.clusters:
        ret.append("Clusters are still attached to %s %s." %
                   (dbbranch.branch_type, dbbranch.name))
    if dbbranch.trackers:
        ret.append("%s %s is tracked by %s." %
                   (dbbranch.branch_type, dbbranch.name,
                    [str(t.name) for t in dbbranch.trackers]))
    return ret

def remove_branch(config, logger, dbbranch):
    session = object_session(dbbranch)
    deps = get_branch_dependencies(dbbranch)
    if deps:
        raise ArgumentError("\n".join(deps))

    session.delete(dbbranch)

    domain = TemplateDomain(dbbranch, logger=logger)
    key = CompileKey(domain=dbbranch.name, logger=logger)
    # Can this fail?  Is recovery needed?
    try:
        lock_queue.acquire(key)
        for dir in domain.directories():
            remove_dir(dir, logger=logger)
    finally:
        lock_queue.release(key)

    kingdir = config.get("broker", "kingdir")
    try:
        run_git(["branch", "-D", dbbranch.name],
                path=kingdir, logger=logger)
    except ProcessException, e:
        logger.warning("Error removing branch %s from template-king, "
                       "proceeding anyway: %s", dbbranch.name, e)
