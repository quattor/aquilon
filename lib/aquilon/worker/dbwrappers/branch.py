# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016  Contributor
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

import logging
import os.path
import re
from tempfile import mkdtemp

from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql import and_, or_

from aquilon.exceptions_ import (ArgumentError, AuthorizationException,
                                 ProcessException)
from aquilon.config import Config
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import (Domain, Sandbox, Branch, CompileableMixin,
                                Archetype, Personality, PersonalityStage,
                                User)
from aquilon.utils import remove_dir, validate_template_name
from aquilon.worker.dbwrappers.user_principal import get_user_principal
from aquilon.worker.processes import run_git
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.domain import TemplateDomain

VERSION_RE = re.compile(r'^[-_.a-zA-Z0-9]*$')


def parse_sandbox(session, sandbox, default_author=None):
    if "/" in sandbox:
        author, branch = sandbox.split("/", 1)
        dbauthor = User.get_unique(session, author, compel=True)
    else:
        branch = sandbox
        if default_author:
            dbauthor = User.get_unique(session, default_author, compel=True)
        else:
            dbauthor = None

    # This function may be called when the branch does not exist (yet) in the
    # DB, so we need to do the normalization manually
    branch = AqStr.normalize(branch)

    return (branch, dbauthor)


def get_branch_and_author(session, domain=None, sandbox=None, branch=None,
                          compel=False):
    dbbranch = None
    dbauthor = None

    if domain:
        dbbranch = Domain.get_unique(session, domain, compel=True)
    elif branch:
        dbbranch = Branch.get_unique(session, branch, compel=True)
    elif sandbox:
        try:
            author, name = sandbox.split("/", 1)
        except ValueError:
            raise ArgumentError("Expected sandbox as 'author/branch', author "
                                "name and branch name separated by a slash.")
        dbbranch = Sandbox.get_unique(session, name, compel=True)
        dbauthor = User.get_unique(session, author, compel=True)
    elif compel:
        raise ArgumentError("Please specify either sandbox or domain.")

    return (dbbranch, dbauthor)


def force_my_sandbox(session, dbuser, sandbox):
    if not dbuser.realm.trusted:
        raise AuthorizationException("{0} is not trusted to handle "
                                     "sandboxes.".format(dbuser.realm))

    sandbox, dbauthor = parse_sandbox(session, sandbox,
                                      default_author=dbuser.name)
    sandbox = AqStr.normalize(sandbox)

    # User used the name/branch syntax - that's fine.  They can't
    # do anything on behalf of anyone else, though, so error if the
    # user given is anyone else.
    if dbauthor.name != dbuser.name:
        raise ArgumentError("Principal {0!s} cannot add or get a sandbox "
                            "on behalf of '{1!s}'."
                            .format(dbuser, dbauthor))

    return (sandbox, dbauthor)


def get_branch_dependencies(dbbranch):
    """Returns a list of strings describing how a branch is being used.

    If there are no dependencies then an empty list is returned.

    """
    session = object_session(dbbranch)
    ret = []

    for cls_ in CompileableMixin.__subclasses__():
        q = session.query(*inspect(cls_).mapper.primary_key)
        q = q.filter(cls_.branch_id == dbbranch.id)
        cnt = q.count()
        if cnt:
            ret.append("{0} {1!s}s are still attached to {2:l}."
                       .format(cnt, cls_._get_class_label().lower(), dbbranch))

    if dbbranch.trackers:
        ret.append("%s is tracked by %s." %
                   (format(dbbranch), [t.name for t in dbbranch.trackers]))
    return ret


def add_branch(session, config, dbuser, cls_, branch, **arguments):
    if cls_ == Domain:
        label = "--domain"
    else:
        label = "--sandbox"
    validate_template_name(label, branch)

    try:
        run_git(["check-ref-format", "--branch", branch])
    except ProcessException:
        raise ArgumentError("'%s' is not a valid git branch name." % branch)

    Branch.get_unique(session, branch, preclude=True)

    compiler = config.get("panc", "pan_compiler")
    dbbranch = cls_(name=branch, owner=dbuser, compiler=compiler, **arguments)

    if config.has_option("broker", "trash_branch"):
        trash_branch = config.get("broker", "trash_branch")
        if dbbranch.name == trash_branch:
            raise ArgumentError("The branch name %s is reserved." % branch)

    session.add(dbbranch)
    return dbbranch


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
        hash = run_git(["rev-parse", "--verify", dbbranch.name],
                       path=kingdir, logger=logger)
        hash = hash.strip()
        logger.info("{0} head commit was: {1!s}".format(dbbranch, hash))
        run_git(["branch", "-D", dbbranch.name],
                path=kingdir, logger=logger)
    except ProcessException as e:
        logger.warning("Error removing branch %s from template-king, "
                       "proceeding anyway: %s", dbbranch.name, e)


def search_branch_query(config, session, cls, owner=None, compiler_version=None,
                        autosync=None, validated=None, used=None,
                        compileable=None, **_):
    q = session.query(cls)
    if owner:
        dbowner = get_user_principal(session, owner)
        q = q.filter_by(owner=dbowner)

    if compiler_version:
        if not VERSION_RE.match(compiler_version):
            raise ArgumentError("Invalid characters in compiler version")
        compiler = config.get("panc", "pan_compiler",
                              vars={'version': compiler_version})
        q = q.filter_by(compiler=compiler)

    if autosync is not None:
        q = q.filter_by(autosync=autosync)

    if validated is not None:
        q = q.filter_by(is_sync_valid=validated)

    if used is not None:
        filters = []
        for subcls in CompileableMixin.__subclasses__():
            subq = session.query(subcls.branch_id)
            subq = subq.distinct()

            if compileable:
                subq = subq.join(PersonalityStage, Personality, Archetype)
                subq = subq.filter_by(is_compileable=True)

            if used:
                filters.append(cls.id.in_(subq.subquery()))
            else:
                filters.append(~cls.id.in_(subq.subquery()))

        if used:
            q = q.filter(or_(*filters))
        else:
            q = q.filter(and_(*filters))

    return q


def expand_compiler(config, compiler_version):
    if not VERSION_RE.match(compiler_version):
        raise ArgumentError("Invalid characters in compiler version")
    compiler = config.get("panc", "pan_compiler",
                          vars={'version': compiler_version})
    if not os.path.exists(compiler):
        raise ArgumentError("Compiler not found at '%s'" % compiler)
    return compiler


def has_compileable_objects(dbbranch):
    session = object_session(dbbranch)
    used = False

    for cls_ in CompileableMixin.__subclasses__():
        q = session.query(*inspect(cls_).mapper.primary_key)
        q = q.filter(cls_.branch_id == dbbranch.id)
        q = q.join(PersonalityStage, Personality, Archetype)
        q = q.filter_by(is_compileable=True)

        used |= q.count() > 0

        # Short circuit
        if used:
            break

    return used


def merge_into_trash(config, logger, branch, merge_msg, loglevel=logging.INFO):
    trash_branch = config.get("broker", "trash_branch")
    kingdir = config.get("broker", "kingdir")
    rundir = config.get("broker", "rundir")

    temp_msg = []
    temp_msg.append("Empty commit to make sure there will be a merge ")
    temp_msg.append("commit even if the target branch is already merged.")

    try:
        run_git(["show-ref", "--verify", "--quiet", "refs/heads/" + branch],
                path=kingdir, logger=logger, loglevel=loglevel)
    except ProcessException as e:
        logger.client_info("Branch %s does not exist in template-king." %
                           branch)
        return

    tempdir = mkdtemp(prefix="trash_", suffix="_%s" % branch, dir=rundir)

    try:
        run_git(["clone", "--shared", "--branch", trash_branch, "--",
                 kingdir, trash_branch], path=tempdir, logger=logger,
                loglevel=loglevel)

        temprepo = os.path.join(tempdir, trash_branch)

        # If branch is already merged into trash, then we need to force a
        # commit that can be merged
        hash = run_git(["commit-tree", "origin/" + branch + "^{tree}",
                        "-p", trash_branch, "-p", "origin/" + branch,
                        "-m", "\n".join(temp_msg)],
                       path=temprepo, logger=logger, loglevel=loglevel)
        hash = hash.strip()
        run_git(["merge", "-s", "ours", hash, "-m", merge_msg],
                path=temprepo, logger=logger, loglevel=loglevel)
        run_git(["push", "origin", trash_branch], path=temprepo, logger=logger,
                loglevel=loglevel)
    except ProcessException as e:
        raise ArgumentError("\n%s%s" % (e.out, e.err))
    finally:
        remove_dir(tempdir, logger=logger)


def sync_domain(dbdomain, logger):
    """Update templates on disk to match contents of branch in template-king.

    If this domain is tracking another, first update the branch in
    template-king with the latest from the tracking branch.  Also save
    the current (previous) commit as a potential rollback point.

    """
    config = Config()
    kingdir = config.get("broker", "kingdir")
    domaindir = os.path.join(config.get("broker", "domainsdir"), dbdomain.name)

    if dbdomain.tracked_branch:
        # Might need to revisit if using this helper from rollback...
        run_git(["push", ".",
                 "%s:%s" % (dbdomain.tracked_branch.name, dbdomain.name)],
                path=kingdir, logger=logger)

    logger.client_info("Updating the checked out copy of {0:l}..."
                       .format(dbdomain))

    run_git(["fetch", "--prune"], path=domaindir, logger=logger)
    if dbdomain.tracked_branch:
        out = run_git(["rev-list", "-n", "1", "HEAD"],
                      path=domaindir, logger=logger)
        rollback_commit = out.strip()

    with CompileKey(domain=dbdomain.name, logger=logger):
        run_git(["reset", "--hard", "origin/%s" % dbdomain.name],
                path=domaindir, logger=logger)

    if dbdomain.tracked_branch:
        dbdomain.rollback_commit = rollback_commit
