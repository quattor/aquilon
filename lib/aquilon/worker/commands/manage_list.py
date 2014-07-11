# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Contains the logic for `aq manage --list`."""

from collections import defaultdict
import os.path
import re

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import Domain, Sandbox
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.feature import (model_features,
                                               personality_features,
                                               check_feature_template)
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.formats.branch import AuthoredSandbox
from aquilon.worker.locks import CompileKey
from aquilon.worker.processes import run_git
from aquilon.worker.templates.base import Plenary, PlenaryCollection


def validate_branch_commits(dbsource, dbsource_author,
                            dbtarget, dbtarget_author, logger, config):
    """
    Verify that we're not leaving changes behind.

    This function verifies that we're not losing changes in the source sandbox
    or domain that were not committed, not published, or not merged into the
    target sandbox or domain.
    """

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

    # Check if the source has anything uncommitted
    git_status = run_git(["status", "--porcelain"],
                         path=source_path, logger=logger)
    if git_status:
        raise ArgumentError("The source {0:l} contains uncommitted files."
                            .format(dbsource))

    # Get latest source commit and tree ID
    source_commit = run_git(['rev-parse', '--verify', '-q', 'HEAD^{commit}'],
                            path=source_path, logger=logger)
    source_commit = source_commit.strip()
    source_tree = run_git(['rev-parse', '--verify', '-q', 'HEAD^{tree}'],
                          path=source_path, logger=logger)
    source_tree = source_commit.strip()
    if not source_commit or not source_tree:  # pragma: no cover
        raise ArgumentError("Unable to retrieve the last commit information "
                            "from source {0:l}.".format(dbsource))

    # Verify that the source is fully published, i.e. template-king has the same
    # commit
    kingdir = config.get("broker", "kingdir")
    try:
        king_commit = run_git(['rev-parse', '--verify', '-q',
                               dbsource.name + '^{commit}'],
                              path=kingdir, logger=logger)
        king_commit = king_commit.strip()
    except ProcessException as pe:
        if pe.code != 1:
            raise
        else:
            king_commit = None
    if king_commit != source_commit:
        raise ArgumentError("The latest commit of {0:l} has not been "
                            "published to template-king yet.".format(dbsource))

    # Check if target branch has the latest source commit
    try:
        filterre = re.compile('^' + source_commit + '$')
        found = run_git(['rev-list', 'HEAD'], filterre=filterre,
                        path=target_path, logger=logger)
    except ProcessException as pe:
        if pe.code != 128:
            raise
        else:
            found = None

    if not found:
        # If the commit itself was not found, try to check if the two heads
        # point to the same tree object, and the difference is only in history
        # (e.g. merging the same sandbox into different domains will create
        # different merge commits).
        target_tree = run_git(['rev-parse', '--verify', '-q', 'HEAD^{tree}'],
                              path=target_path, logger=logger)
        target_tree = target_tree.strip()
        found = target_tree == source_tree

    if not found:
        raise ArgumentError("The target {0:l} does not contain the latest "
                            "commit from source {1:l}.".format(dbtarget,
                                                               dbsource))


class CommandManageList(BrokerCommand):

    required_parameters = ["list"]

    def get_objects(self, session, list, **arguments):  # pylint: disable=W0613
        check_hostlist_size(self.command, self.config, list)

        dbhosts = hostlist_to_hosts(session, list)

        failed = []

        dbsource, dbsource_author = validate_branch_author(dbhosts)
        for dbhost in dbhosts:
            # check if any host in the list is a cluster node
            if dbhost.cluster:
                failed.append("Cluster nodes must be managed at the "
                              "cluster level; {0} is a member of {1:l}."
                              .format(dbhost.fqdn, dbhost.cluster))

        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))

        return (dbsource, dbsource_author, dbhosts)

    def render(self, session, logger, domain, sandbox, force, **arguments):
        dbbranch, dbauthor = get_branch_and_author(session, logger,
                                                   domain=domain,
                                                   sandbox=sandbox, compel=True)
        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing objects to {0:l} is not allowed."
                                .format(dbbranch))

        dbsource, dbsource_author, objects = self.get_objects(session,
                                                              **arguments)

        if not force:
            validate_branch_commits(dbsource, dbsource_author,
                                    dbbranch, dbauthor, logger, self.config)

            if isinstance(dbbranch, Domain):
                features = defaultdict(set)
                personalities = set()
                for dbobj in objects:
                    pers = dbobj.personality
                    arch = pers.archetype

                    personalities.add(pers)
                    if hasattr(dbobj, 'hardware_entity'):
                        features[arch].update(model_features(dbobj.hardware_entity.model,
                                                             arch, pers))
                for pers in personalities:
                    pre, post = personality_features(pers)
                    features[pers.archetype].update(pre)
                    features[pers.archetype].update(post)

                for dbarch, featureset in features.items():
                    for dbfeature in featureset:
                        check_feature_template(self.config, dbarch, dbfeature,
                                               dbbranch)

        plenaries = PlenaryCollection(logger=logger)

        for dbobj in objects:
            plenaries.append(Plenary.get_plenary(dbobj))

            dbobj.branch = dbbranch
            dbobj.sandbox_author = dbauthor

        session.flush()

        # We're crossing domains, need to lock everything.
        with CompileKey.merge([CompileKey(domain=dbsource.name, logger=logger),
                               CompileKey(domain=dbbranch.name, logger=logger)]):
            plenaries.stash()
            try:
                plenaries.write(locked=True)
            except:
                plenaries.restore_stash()
                raise

        return
