# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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

import os
import re

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import Domain, Sandbox, Branch
from aquilon.worker.dbwrappers.user_principal import get_user_principal
from aquilon.worker.processes import remove_dir, run_git
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.domain import TemplateDomain

VERSION_RE = re.compile(r'^[-_.a-zA-Z0-9]*$')


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
        ret.append("Hosts are still attached to {0:l}.".format(dbbranch))
    if dbbranch.clusters:
        ret.append("Clusters are still attached to {0:l}.".format(dbbranch))
    if dbbranch.trackers:
        ret.append("%s is tracked by %s." %
                   (format(dbbranch), [str(t.name) for t in dbbranch.trackers]))
    return ret


def remove_branch(config, logger, dbbranch):
    session = object_session(dbbranch)
    deps = get_branch_dependencies(dbbranch)
    if deps:
        raise ArgumentError("\n".join(deps))

    session.delete(dbbranch)

    domain = TemplateDomain(dbbranch, logger=logger)
    # Can this fail?  Is recovery needed?
    with CompileKey(domain=dbbranch.name, logger=logger):
        for dir in domain.directories():
            remove_dir(dir, logger=logger)

    kingdir = config.get("broker", "kingdir")
    try:
        run_git(["branch", "-D", dbbranch.name],
                path=kingdir, logger=logger)
    except ProcessException, e:
        logger.warning("Error removing branch %s from template-king, "
                       "proceeding anyway: %s", dbbranch.name, e)


def search_branch_query(config, session, cls, owner=None, compiler_version=None,
                        autosync=None, validated=None, **arguments):
    q = session.query(cls)
    if owner:
        dbowner = get_user_principal(session, owner)
        q = q.filter_by(owner=dbowner)
    if compiler_version:
        if not VERSION_RE.match(compiler_version):
            raise ArgumentError("Invalid characters in compiler version")
        compiler = config.get("panc", "pan_compiler", raw=True) % {
            'version': compiler_version}
        q = q.filter_by(compiler=compiler)
    if autosync is not None:
        q = q.filter_by(autosync=autosync)
    if validated is not None:
        q = q.filter_by(is_sync_valid=validated)
    return q


def expand_compiler(config, compiler_version):
    if not VERSION_RE.match(compiler_version):
        raise ArgumentError("Invalid characters in compiler version")
    compiler = config.get("panc", "pan_compiler", raw=True) % {
        'version': compiler_version}
    if not os.path.exists(compiler):
        raise ArgumentError("Compiler not found at '%s'" % compiler)
    return compiler
