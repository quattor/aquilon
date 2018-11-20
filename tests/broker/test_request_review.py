#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Module for testing the request review command."""

import os
from shutil import rmtree
from subprocess import PIPE
from subprocess import Popen

import unittest

from brokertest import TestBrokerCommand

if __name__ == "__main__":
    import utils
    utils.import_depends()


class TestRequestReview(TestBrokerCommand):

    @classmethod
    def setUpClass(cls):
        super(TestRequestReview, cls).setUpClass()

        # Run "make clean" on templates before anything else.
        testdir = os.path.join(cls.sandboxdir, "reviewtest1", "t")
        if os.path.exists(os.path.join(testdir, "Makefile")):
            p = Popen(('/usr/bin/make', 'clean'),
                      cwd=testdir, env=cls.gitenv(
                    env={'PATH': '/bin:/usr/bin'}),
                      stdout=PIPE, stderr=PIPE)
            (out, err) = p.communicate()
            cls.assertEqual(p.returncode, 0,
                            "Non-zero return code running "
                            "make clean in sandbox, "
                            "STDOUT:\n@@@'{}'\n@@@\nSTDERR:\n@@@'{}'@@@\n"
                            .format(out, err))

    def test_111_make_change(self):
        sandboxdir = os.path.join(self.sandboxdir, "reviewtest1")
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="reviewtest1")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by unittest\n")

        with open(template, 'w') as f:
            f.writelines(contents)

        self.gitcommand(["commit", "-a", "-m", "added unittest comment"],
                        cwd=sandboxdir)

    def test_121_publish_reviewtest1_sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "reviewtest1")
        self.successtest(["publish", "--branch", "reviewtest1"],
                         env=self.gitenv(), cwd=sandboxdir)
        # FIXME: Check the branch on the broker directly?

    def test_131_publish_reviewtest1_sandbox_no_review_created(self):
        command = ["show_review",
                   "--source", "reviewtest1",
                   "--target", "prod"]
        self.notfoundtest(command)

    def test_141_verify_reviewtest1(self):
        sandboxdir = os.path.join(self.sandboxdir, "reviewtest1")
        p = Popen(["/bin/rm", "-rf", sandboxdir], stdout=1, stderr=2)
        p.wait()
        self.successtest(["get", "--sandbox", "reviewtest1"])
        self.assertTrue(os.path.exists(sandboxdir))
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="reviewtest1")
        self.assertTrue(os.path.exists(template),
                        "aq get did not retrive '%s'" % template)
        with open(template) as f:
            contents = f.readlines()
        self.assertEqual(contents[-1], "#Added by unittest\n")

    def test_151_show_review(self):
        review_head = self.head_commit("reviewtest1")
        command = ["show_review",
                   "--source", "reviewtest1",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
              Source Sandbox: reviewtest1
                Published Commit: %s
              Code Review URL: TEST_GERRIT_PR_URL
              Testing Status: Untested
              Approval Status: No decision
            """ % review_head,
                           command)

    def test_161_add_reviewtest_domain(self):
        command = ["add_domain",
                   "--domain", "reviewtestdomain",
                   "--start", "prod"] + self.valid_just_tcm
        self.successtest(command)

    def test_171_reviewtest1_sandbox_no_review_created(self):
        command = ["show_review",
                   "--source", "reviewtest1",
                   "--target", "reviewtestdomain"]
        self.notfoundtest(command)

    def test_181_request_review(self):
        command = ["request_review",
                   "--source", "reviewtest1",
                   "--target", "reviewtestdomain"]
        self.successtest(command)

    def test_191_show_review(self):
        review_head = self.head_commit("reviewtest1")
        command = ["show_review",
                   "--source", "reviewtest1",
                   "--target", "reviewtestdomain"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: reviewtestdomain
              Source Sandbox: reviewtest1
                Published Commit: %s
              Code Review URL: TEST_GERRIT_PR_URL
              Testing Status: Untested
              Approval Status: No decision
            """ % review_head,
                           command)

    def test_999_cleanup(self):
        self.statustest(["del_sandbox", "--sandbox", "reviewtest1"])
        sandboxdir = os.path.join(self.sandboxdir, "reviewtest1")
        rmtree(sandboxdir, ignore_errors=True)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRequestReview)
    unittest.TextTestRunner(verbosity=2).run(suite)
