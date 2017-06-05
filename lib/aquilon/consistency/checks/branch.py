#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014  Contributor
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

import logging

from aquilon.consistency.checker import ConsistencyChecker
from aquilon.aqdb.model.branch import Branch
from aquilon.worker.processes import run_git
from aquilon.worker.dbwrappers.branch import merge_into_trash


class BranchChecker(ConsistencyChecker):
    """
    Branch Consistency Checker

    This module performs validation that is common for all branches (both
    domains and sandboxes) in template-king.
    """

    def check(self, repair=False):
        # Find all of the branches that are listed in the database
        db_branches = {}
        for branch in self.session.query(Branch):
            db_branches[branch.name] = branch

        # Find all of the branches that are in the template king, this
        # includes both domains and sandbox's
        kingdir = self.config.get("broker", "kingdir")
        out = run_git(['for-each-ref', '--format=%(refname:short)',
                       'refs/heads'], path=kingdir, loglevel=logging.DEBUG)
        git_branches = set(out.splitlines())

        # The trash branch is special
        if self.config.has_option("broker", "trash_branch"):
            git_branches.remove(self.config.get("broker", "trash_branch"))

        # Branches in the database and not in the template-king
        for branch in set(db_branches.keys()).difference(git_branches):
            self.failure(branch, format(db_branches[branch]),
                         "found in the database but not in template-king")
            # No repair mode. We consider AQDB more canonical than
            # template-king, so we should not delete the DB object, and we don't
            # have any information how to restore the branch in template-king.

        # Branches in the template-king and not in the database
        for branch in git_branches.difference(db_branches.keys()):
            if repair:
                self.logger.info("Deleting branch %s", branch)

                merge_msg = []
                merge_msg.append("Delete orphaned branch %s" % branch)
                merge_msg.append("")
                merge_msg.append("The consistency checker found this branch to be ")
                merge_msg.append("orphaned.")

                if self.config.has_option("broker", "trash_branch"):
                    merge_into_trash(self.config, self.logger, branch,
                                     "\n".join(merge_msg),
                                     loglevel=logging.DEBUG)
                run_git(['branch', '-D', branch], path=kingdir,
                        loglevel=logging.DEBUG)
            else:
                self.failure(branch, "Branch %s" % branch,
                             "found in template-king but not in the database")
