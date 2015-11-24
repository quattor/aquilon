#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015  Contributor
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
from subprocess import Popen, PIPE
from shutil import rmtree

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestConsistency(TestBrokerCommand):
    def test_010_add_filesystem_only(self):
        # Create a dummy domain directory, not in the database and neither in
        # template-king
        dir = os.path.join(self.config.get("broker", "domainsdir"),
                           'filesystem-only')
        try:
            os.makedirs(dir, 0o755)
        except OSError:
            # Directory may already exist
            pass

    def test_020_add_branch_only(self):
        kingdir = self.config.get("broker", "kingdir")
        self.gitcommand(["branch", "branch-only", "prod"], cwd=kingdir)

    def test_030_add_domain_no_fileystem(self):
        self.successtest(["add_domain", "--domain", "domain-no-filesystem"])
        dir = os.path.join(self.config.get("broker", "domainsdir"),
                           "domain-no-filesystem")
        rmtree(dir)

    def test_040_add_domain_no_template_king(self):
        kingdir = self.config.get("broker", "kingdir")
        self.successtest(["add_domain", "--domain", "domain-no-template-king"])
        self.gitcommand(["branch", "-D", "domain-no-template-king"], cwd=kingdir)

    def test_050_add_sandbox_no_template_king(self):
        kingdir = self.config.get("broker", "kingdir")
        self.successtest(["add_sandbox", "--sandbox",
                          "sandbox-no-template-king", "--noget"])
        self.gitcommand(["branch", "-D", "sandbox-no-template-king"], cwd=kingdir)

    def test_100_consistency(self):
        # Run the checker and collect its output
        command = 'aqd_consistency_check.py'
        dir = os.path.dirname(os.path.realpath(__file__))
        checker = os.path.join(dir, '..', '..', 'sbin', command)
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        out, err = Popen(checker, stdout=PIPE, stderr=PIPE,
                         env=env).communicate()
        self.assertEmptyErr(err, command)

        # 1. BranchChecker
        #
        # "Domain XXXX found in the database but not in template-king"
        self.matchoutput(out, "Domain domain-no-template-king found in the "
                         "database but not in template-king", command)
        self.matchoutput(out, "Sandbox sandbox-no-template-king found in the "
                         "database but not in template-king", command)
        self.matchclean(out, "Domain prod found", command)

        # "Branch XXXX found in template-king but not in the database"
        self.matchoutput(out, "Branch branch-only found in template-king "
                         "but not in the database", command)

        # The trash branch does not exist in the DB and that's OK
        trash = self.config.get("broker", "trash_branch")
        self.matchclean(out, trash, command)

        # 2. SandboxChecker
        #
        # "Sandbox XXXX found in the database but not on the filesystem"
        self.matchoutput(out, "Sandbox sandbox-no-template-king found in the "
                         "database but not on the filesystem", command)
        self.matchclean(out, "Sandbox managetest1 found", command)

        # 3. DomainChecker
        #
        # "Branch XXXX found in the database but not on the filesystem"
        self.matchoutput(out, "Domain domain-no-filesystem found in the "
                         "database but not on the filesystem", command)
        self.matchclean(out, "Domain prod found in the database", command)

        # "Domain XXXX found on filesystem (%s) but not in database"
        dir = os.path.join(self.config.get("broker", "domainsdir"),
                           "filesystem-only")
        self.matchoutput(out, "Domain filesystem-only found on the filesystem "
                         "(%s) but not in the database" % dir,
                         command)
        self.matchclean(out, "Domain prod found", command)

    def test_110_repair_branch(self):
        command = 'aqd_consistency_check.py'
        dir = os.path.dirname(os.path.realpath(__file__))
        checker = os.path.join(dir, '..', '..', 'sbin', command)
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        out, err = Popen([checker, "--repair", "--only=BranchChecker"],
                         stdout=PIPE, stderr=PIPE, env=env).communicate()
        self.assertEmptyErr(err, command)

        self.matchoutput(out, "Deleting branch branch-only", command)

        # The trash branch should not get deleted
        trash = self.config.get("broker", "trash_branch")
        self.matchclean(out, trash, command)

    def test_115_verify_delete_orphaned_branch(self):
        kingdir = self.config.get("broker", "kingdir")
        command = ["log", "--no-color", "-n", "1", self.config.get("broker",
                                                                   "trash_branch")]
        out, err = self.gitcommand(command, cwd=kingdir)
        self.matchoutput(out, "Delete orphaned branch branch-only", command)

    def test_120_repair_domain(self):
        command = 'aqd_consistency_check.py'
        dir = os.path.dirname(os.path.realpath(__file__))
        checker = os.path.join(dir, '..', '..', 'sbin', command)
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        out, err = Popen([checker, "--repair", "--only=DomainChecker"],
                         stdout=PIPE, stderr=PIPE, env=env).communicate()
        self.assertEmptyErr(err, command)

        dir = os.path.join(self.config.get("broker", "domainsdir"),
                           "filesystem-only")
        self.matchoutput(out, "Removing %s" % dir, command)
        self.assertFalse(os.path.exists(dir))

        dir = os.path.join(self.config.get("broker", "domainsdir"),
                           "domain-no-filesystem")
        self.matchoutput(out, "Checking out domain domain-no-filesystem",
                         command)
        self.assertTrue(os.path.exists(dir))

    def test_800_cleanup(self):
        self.noouttest(["update_domain", "--domain", "domain-no-filesystem",
                        "--archived"])
        self.statustest(["del_domain", "--domain", "domain-no-filesystem",
                         "--justification", "tcm=123456"])

        self.noouttest(["update_domain", "--domain", "domain-no-template-king",
                        "--archived"])
        self.statustest(["del_domain", "--domain", "domain-no-template-king",
                         "--justification", "tcm=123456"])

        self.statustest(["del_sandbox", "--sandbox", "sandbox-no-template-king"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConsistency)
    unittest.TextTestRunner(verbosity=2).run(suite)
