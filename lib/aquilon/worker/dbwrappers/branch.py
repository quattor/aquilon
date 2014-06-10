# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
"""Wrapper to make getting a branch simpler."""

import os
import re

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import (Domain, Sandbox, Branch, Host, Cluster,
                                Archetype, Personality)
from aquilon.worker.dbwrappers.user_principal import get_user_principal
from aquilon.worker.processes import run_git
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.utils import remove_dir

VERSION_RE = re.compile(r'^[-_.a-zA-Z0-9]*$')


def get_branch_and_author(session, domain=None, sandbox=None, branch=None,
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
    session = object_session(dbbranch)
    ret = []

    q = session.query(Host.hardware_entity_id)
    q = q.filter_by(branch=dbbranch)
    if q.count():
        ret.append("Hosts are still attached to {0:l}.".format(dbbranch))

    q = session.query(Cluster.id)
    q = q.filter_by(branch=dbbranch)
    if q.count():
        ret.append("Clusters are still attached to {0:l}.".format(dbbranch))

    if dbbranch.trackers:
        ret.append("%s is tracked by %s." %
                   (format(dbbranch), [str(t.name) for t in dbbranch.trackers]))
    return ret


def remove_branch(config, logger, dbbranch, dbauthor=None):
    session = object_session(dbbranch)
    deps = get_branch_dependencies(dbbranch)
    if deps:
        raise ArgumentError("\n".join(deps))

    session.delete(dbbranch)

    domain = TemplateDomain(dbbranch, dbauthor, logger=logger)
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


def has_compileable_objects(dbbranch):
    session = object_session(dbbranch)

    q1 = session.query(Cluster.id)
    q1 = q1.filter_by(branch=dbbranch)
    q1 = q1.join(Personality, Archetype)
    q1 = q1.filter_by(is_compileable=True)

    q2 = session.query(Host.hardware_entity_id)
    q2 = q2.filter_by(branch=dbbranch)
    q2 = q2.join(Personality, Archetype)
    q2 = q2.filter_by(is_compileable=True)

    return q1.count() or q2.count()
