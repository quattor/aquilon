#!/usr/bin/env python
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

from aquilon.consistency.checker import ConsistencyChecker
from aquilon.aqdb.model.branch import Branch
from aquilon.worker.processes import run_git


class BranchChecker(ConsistencyChecker):
    """Branch Consistancy Checker

    Branches exist in three places, the database (as domains/sandboxes),
    git (as branches) and in the fileling system.  This checker attempts
    to ensure that all three sources of information are consistant.

    We always use the database (gold!) as a point of comparison.
    """

    def check(self):
        # Find all of the branchs that are listed in the database
        db_branches = set()
        db_domains = set()
        db_sandboxs = set()
        branch_type = dict()
        for branch in self.session.query(Branch):
            if branch.branch_type == 'domain':
                db_domains.add(branch.name)
                branch_type[branch.name] = 'Domain'
            elif branch.branch_type == 'sandbox':
                db_sandboxs.add(branch.name)
                branch_type[branch.name] = 'Sandbox'
            else:
                self.failure (1, "Branch type", "%s is unknonwn for %s."
                              % (branch.branch_type, branch.name))
                continue
            db_branches.add(branch.name)

        # Find all of the branches that are in the template king, this
        # includes both domains and sandbox's
        kingdir = self.config.get("broker", "kingdir")
        out = run_git(['git', 'for-each-ref', '--format=%(refname:short)',
                       'refs/heads'], path=kingdir)
        git_branches = set(out.splitlines())

        # Find all of the checked out sanbox's
        fs_sandboxs = set()
        fsinfo = {}
        templatesdir = self.config.get("broker", "templatesdir")
        for (root, dirs, files) in os.walk(templatesdir):
            if root is templatesdir:
                if files:
                    self.failure (1, "Template dir", "%s contains files" % root)
            else:
                if files:
                    self.failure (1, "Template dir", "%s contains files" % root)
                user = os.path.split(root)[-1]
                for dir in dirs:
                    fs_sandboxs.add(dir)
                    fsinfo[dir] = os.path.join(root, dir)
                # Prevent any furher recursion
                dirs[:] = []

        # Find all of the domains
        fs_domains = set()
        domainsdir = self.config.get("broker", "domainsdir")
        for (root, dirs, files) in os.walk(domainsdir):
            if files:
                self.failure (1, "Domains dir", "%s contains files" % root)
            for dir in dirs:
                fs_domains.add(dir)
                fsinfo[dir] = os.path.join(root, dir)
            # Prevent any furher recursion
            dirs[:] = []

        #######################################################################
        #
        # Database (domains+sandbox's) == Git (domains+sandbox's)
        #

        # Branches in the database and not in the template-king
        for branch in db_branches.difference(git_branches):
            self.failure(branch, "%s %s" % (branch_type[branch], branch),
                         "found in database and not template-king")

        # Branches in the template-king and not in the database
        for branch in git_branches.difference(db_branches):
            self.failure(branch, "Branch %s" % branch,
                         "found in template-king and not database")

        #######################################################################
        #
        # Database (sandbox) == Filesystem (sandbox)
        #

        # Branches in the database and not in the fileing system
        for branch in db_sandboxs.difference(fs_sandboxs):
            self.failure(branch, "Sandbox %s" % branch,
                             "found in database but not on filesystem")

        # Note to future self:
        #   The following check is techncally not needed as we do not delete
        #   the sandbox from the fileing system when the del_sanbox command
        #   is run.  However, the following has been left just in case we
        #   decide to have a change of heart about this practice.
        #
        # Branchs on fileing system but not in the database
        #for branch in fs_sandboxs.difference(db_sandboxs):
        #    self.failure(branch, "Sandbox %s" % branch,
        #                 "found on filesystem (%s) but not in database"
        #                 % fsinfo[branch])

        #######################################################################
        #
        # Database (domains) == Filesystem (domains)
        #

        # Branches in the database and not in the fileing system
        for branch in db_domains.difference(fs_domains):
            self.failure(branch, "Domain %s" % branch,
                             "found in database but not on filesystem")

        # Branchs on fileing system but not in the database
        for branch in fs_domains.difference(db_domains):
            self.failure(branch, "Domain %s" % branch,
                         "found on filesystem (%s) but not in database" %
                         fsinfo[branch])


