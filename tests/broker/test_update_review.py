#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the update review command."""

import os.path
from shutil import copy

import unittest

from brokertest import TestBrokerCommand

if __name__ == "__main__":
    import utils
    utils.import_depends()


class TestUpdateReview(TestBrokerCommand):

    def head_commit(self, sandbox, ref="HEAD"):
        sandboxdir = os.path.join(self.sandboxdir, sandbox)
        head, _ = self.gitcommand(["rev-parse", "%s^{commit}" % ref],
                                  cwd=sandboxdir)
        head = head.strip()
        return head

    # create sandbox
    def test_110_add_update_review_sandbox(self):
        command = ["add_sandbox",
                   "--sandbox", "{}/update-review-sandbox".format(self.user)]
        out, err = self.successtest(command)
        self.matchoutput(err, "Creating {}".format(self.sandboxdir), command)
        sandboxdir = os.path.join(self.sandboxdir, "update-review-sandbox")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.assertTrue(os.path.isdir(sandboxdir),
                        "Expected directory '{}' to exist".format(sandboxdir))

    # add commit to sandbox
    def test_120_add_files(self):
        src_dir = os.path.join(self.config.get("unittest", "datadir"),
                               "update-review-sandbox")
        sandboxdir = os.path.join(self.sandboxdir, "update-review-sandbox")
        for root, _, files in os.walk(src_dir):
            relpath = root[len(src_dir) + 1:]
            dst_dir = os.path.join(sandboxdir, relpath)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file in files:
                copy(os.path.join(root, file), os.path.join(dst_dir, file))
                self.gitcommand(["add", os.path.join(relpath, file)],
                                cwd=sandboxdir)
        self.gitcommand(["commit", "-a", "-m", "Added unittest files"],
                        cwd=sandboxdir)

    # aq publish with --review
    def test_130_publish_review(self):
        sandboxdir = os.path.join(self.sandboxdir, "update-review-sandbox")
        self.successtest(["publish",
                          "--branch", "update-review-sandbox",
                          "--review"],
                         env=self.gitenv(), cwd=sandboxdir)

    # show review
    def test_140_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: TEST_GERRIT_PR_URL
              Testing Status: Untested
              Approval Status: No decision
            """.format(update_review_sandbox_head),
                           command)

    # update review with url
    def test_150_update_review_url(self):
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--review_url", "http://review.example.org/changes/1234"]
        self.noouttest(command)

    # check url
    def test_160_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review test succeeded
    def test_170_update_review_testing(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--target_commit_tested", prod_head,
                   "--testing_url", "http://ci.example.org/builds/5678",
                   "--testing_succeeded"]
        self.noouttest(command)

    # check test state
    def test_180_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Success
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review reset test
    def test_190_update_review_testing(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--target_commit_tested", prod_head,
                   "--testing_url", "http://ci.example.org/builds/5678",
                   "--reset_testing"]
        self.noouttest(command)

    # check test state
    def test_200_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review test failed
    def test_210_update_review_testing(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--target_commit_tested", prod_head,
                   "--testing_url", "http://ci.example.org/builds/5678",
                   "--testing_failed"]
        self.noouttest(command)

    # check test state
    def test_220_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Failed
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review reset test
    def test_230_update_review_testing_reset(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--reset_testing"]
        self.noouttest(command)

    # check test state
    def test_240_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review approved
    def test_250_update_review_approval(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--approved"]
        self.noouttest(command)

    # check review state
    def test_260_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: Approved
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review reset review
    def test_270_update_review_reset(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--reset"]
        self.noouttest(command)

    # check review state
    def test_280_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review denied
    def test_u119_update_review_denied(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--denied"]
        self.noouttest(command)

    # check review state
    def test_u120_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: Denied
            """.format(prod_head, update_review_sandbox_head),
                           command)

    # update review reset review
    def test_u121_update_review_reset(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        command = ["update_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod",
                   "--commit_id", update_review_sandbox_head,
                   "--reset"]
        self.noouttest(command)

    # check review state
    def test_u122_show_review(self):
        update_review_sandbox_head = self.head_commit("update-review-sandbox")
        prod_head = self.head_commit("update-review-sandbox",
                                     ref="origin/prod")
        command = ["show_review",
                   "--source", "update-review-sandbox",
                   "--target", "prod"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Review request
              Target Domain: prod
                Tested Commit: {}
              Source Sandbox: update-review-sandbox
                Published Commit: {}
              Code Review URL: http://review.example.org/changes/1234
              Testing Status: Untested
              Approval Status: No decision
            """.format(prod_head, update_review_sandbox_head),
                           command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateReview)
    unittest.TextTestRunner(verbosity=2).run(suite)
