# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2016,2017  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Domain, Sandbox, Host
from aquilon.aqdb.model.feature import hardware_features, host_features
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.feature import check_feature_template
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.formats.branch import AuthoredSandbox
from aquilon.worker.locks import CompileKey
from aquilon.worker.processes import GitRepo
from aquilon.worker.templates import TemplateDomain
from aquilon.worker.dbwrappers.change_management import ChangeManagement


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

    source_repo = GitRepo(source_path, logger)
    target_repo = GitRepo(target_path, logger)
    kingrepo = GitRepo.template_king(logger)

    # Check if the source has anything uncommitted
    git_status = source_repo.run(["status", "--porcelain"])
    if git_status:
        raise ArgumentError("The source {0:l} contains uncommitted files."
                            .format(dbsource))

    # Get latest source commit and tree ID
    source_commit = source_repo.ref_commit()
    source_tree = source_repo.ref_tree()
    if not source_commit or not source_tree:  # pragma: no cover
        raise ArgumentError("Unable to retrieve the last commit information "
                            "from source {0:l}.".format(dbsource))

    # Verify that the source is fully published, i.e. template-king has the same
    # commit
    king_commit = kingrepo.ref_commit(dbsource.name, compel=False)
    if king_commit != source_commit:
        raise ArgumentError("The latest commit of {0:l} has not been "
                            "published to template-king yet.".format(dbsource))

    # Check if target branch has the latest source commit
    found = target_repo.ref_contains_commit(source_commit)

    if not found:
        # If the commit itself was not found, try to check if the two heads
        # point to the same tree object, and the difference is only in history
        # (e.g. merging the same sandbox into different domains will create
        # different merge commits).
        target_tree = target_repo.ref_tree()
        found = target_tree == source_tree

    if not found:
        raise ArgumentError("The target {0:l} does not contain the latest "
                            "commit from source {1:l}.".format(dbtarget,
                                                               dbsource))


class CommandManageList(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["list"]

    def get_objects(self, session, list, **_):
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

    def render(self, session, logger, plenaries, domain, sandbox, force,
               skip_auto_compile, user, justification, reason, **arguments):

        dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
                                                   sandbox=sandbox, compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing objects to {0:l} is not allowed."
                                .format(dbbranch))

        dbsource, dbsource_author, objects = self.get_objects(session,
                                                              logger=logger,
                                                              **arguments)

        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        for obj in objects:
            if isinstance(obj, Host):
                cm.consider(obj)
        cm.validate()

        if isinstance(dbsource, Sandbox) and not dbsource_author and not force:
            raise ArgumentError("Unable to determine location of sandbox due to "
                                "missing user record. Please manually verify "
                                "there are no uncommitted and unpublished "
                                "changes and then re-run using --force.")

        auto_compile = False
        # If target is a sandbox
        if sandbox and isinstance(dbsource, Sandbox) and not skip_auto_compile:
            auto_compile = True
        # If target is a domain
        elif domain and dbbranch.auto_compile and not skip_auto_compile:
            auto_compile = True

        if not force:
            validate_branch_commits(dbsource, dbsource_author,
                                    dbbranch, dbauthor, logger, self.config)

            if isinstance(dbbranch, Domain):
                features = defaultdict(set)
                personality_stages = set()
                for dbobj in objects:
                    dbstage = dbobj.personality_stage

                    personality_stages.add(dbstage)
                    if hasattr(dbobj, 'hardware_entity'):
                        feats = hardware_features(dbstage,
                                                  dbobj.hardware_entity.model)
                        features[dbstage.archetype].update(feats)
                for dbstage in personality_stages:
                    pre, post = host_features(dbstage)
                    features[dbstage.archetype].update(pre)
                    features[dbstage.archetype].update(post)

                for dbarch, featureset in features.items():
                    for dbfeature in featureset:
                        check_feature_template(self.config, dbarch, dbfeature,
                                               dbbranch)

        for dbobj in objects:
            if dbsource != dbbranch:
                logger.client_info("Moving {0:l} from {1:l} to {2:l}"
                                   .format(dbobj, dbsource, dbbranch))
            plenaries.add(dbobj)

            dbobj.branch = dbbranch
            dbobj.sandbox_author = dbauthor

        session.flush()

        # We're crossing domains, need to lock everything.
        with CompileKey.merge([CompileKey(domain=dbsource.name, logger=logger),
                               CompileKey(domain=dbbranch.name, logger=logger)]):
            plenaries.stash()
            try:
                plenaries.write(locked=True)
                if auto_compile:
                    td = TemplateDomain(dbbranch, dbauthor, logger=logger)
                    td.compile(session, only=plenaries.object_templates)
            except:
                plenaries.restore_stash()
                raise
        return
