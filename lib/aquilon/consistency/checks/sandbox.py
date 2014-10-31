#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
from aquilon.aqdb.model.branch import Sandbox


class SandboxChecker(ConsistencyChecker):
    """Sandbox Consistancy Checker"""

    def check(self, repair=False):
        db_sandboxes = {}
        for sandbox in self.session.query(Sandbox):
            db_sandboxes[sandbox.name] = sandbox

        # Find all of the checked out sanbox's
        fs_sandboxes = {}
        templatesdir = self.config.get("broker", "templatesdir")
        for (root, dirs, files) in os.walk(templatesdir):
            if root is templatesdir:
                if files:
                    self.failure(1, "Template dir", "%s contains files" % root)
            else:
                if files:
                    self.failure(1, "Template dir", "%s contains files" % root)
                # user = os.path.split(root)[-1]
                for dir in dirs:
                    fs_sandboxes[dir] = os.path.join(root, dir)
                # Prevent any furher recursion
                dirs[:] = []

        #######################################################################
        #
        # Database (sandbox) == Filesystem (sandbox)
        #

        # Branches in the database and not in the fileing system
        for branch in set(db_sandboxes.keys()).difference(fs_sandboxes.keys()):
            self.failure(branch, format(db_sandboxes[branch]),
                         "found in the database but not on the filesystem")
            # No repair mode - the users can fix missing sandboxes themselves by
            # running "aq get"

        # Note to future self:
        #   The following check is techncally not needed as we do not delete
        #   the sandbox from the fileing system when the del_sanbox command
        #   is run.  However, the following has been left just in case we
        #   decide to have a change of heart about this practice.
        #
        # Branchs on fileing system but not in the database
        # for branch in set(fs_sandboxes.keys()).difference(db_sandboxes.keys()):
        #    self.failure(branch, "Sandbox %s" % branch,
        #                 "found on filesystem (%s) but not in database"
        #                 % fs_sandboxes[branch])
