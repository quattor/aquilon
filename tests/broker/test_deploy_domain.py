#!/usr/bin/env python2.6
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
"""Module for testing the deploy domain command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDeployDomain(TestBrokerCommand):

    def test_100_deploychangetest1domain(self):
        self.successtest(["deploy", "--source", "changetest1",
                          "--target", "deployable",
                          "--comments", "Test comment"])

    def test_110_verifydeploy(self):
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="deployable")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")

    def test_110_verifydeploylog(self):
        kingdir = self.config.get("broker", "kingdir")
        command = ["log", "--no-color", "-n", "1", "deployable"]
        (out, err) = self.gitcommand(command, cwd=kingdir)
        self.matchoutput(out, "User:", command)
        self.matchoutput(out, "Request ID:", command)
        self.matchoutput(out, "Comments: Test comment", command)

        author_name = self.config.get("broker", "user")
        author_email = self.config.get("broker", "git_author_email")
        self.matchoutput(out, "Author: %s <%s>" % (author_name, author_email),
                         command)

    def test_120_deployfail(self):
        command = ["deploy", "--source", "changetest1",
                   "--target", "prod"]
        (out, err) = self.failuretest(command, 4)
        self.matchoutput(err,
                         "Domain prod is under change management control.  "
                         "Please specify --justification.",
                         command)

    def test_120_deploybadjustification(self):
        command = ["deploy", "--source", "changetest1", "--target", "prod",
                   "--justification", "I felt like deploying changes."]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Failed to parse the justification", command)

    def test_130_deploynosync(self):
        self.successtest(["deploy", "--source", "changetest1",
                          "--target", "prod", "--nosync",
                          "--justification", "tcm=12345678",
                          "--comments", "Test comment 2"])

    def test_200_verifynosync(self):
        # The change should be in prod...
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="prod")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")
        # ...but not in the ut-prod tracking domain.
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="ut-prod")
        with open(template) as f:
            contents = f.readlines()
        self.failIfEqual(contents[-1], "#Added by unittest\n")

    def test_210_verifynosynclog(self):
        kingdir = self.config.get("broker", "kingdir")

        # Note: "prod" is a copy of the real thing so limit the amount of
        # history checked to avoid being fooled by real commits

        # The change must be in prod...
        command = ["log", "--no-color", "-n", "1", "prod"]
        (out, err) = self.gitcommand(command, cwd=kingdir)
        self.matchoutput(out, "Justification: tcm=12345678", command)
        self.matchoutput(out, "Comments: Test comment 2", command)

        # ... but not in ut-prod
        command = ["log", "--no-color", "-n", "1", "ut-prod"]
        (out, err) = self.gitcommand(command, cwd=kingdir)
        self.matchclean(out, "tcm=12345678", command)

    def test_300_addadvanced(self):
        self.successtest(["add", "sandbox", "--sandbox", "advanced",
                          "--start", "prod"])

    def test_310_deploy_leftbehind(self):
        command = ["deploy", "--source", "advanced", "--target", "leftbehind"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "You're trying to deploy a sandbox to a domain that "
                         "does not contain the commit where the sandbox was "
                         "branched from.",
                         command)

    def test_320_update_leftbehind(self):
        command = ["deploy", "--source", "prod", "--target", "leftbehind"]
        self.successtest(command)

    def test_330_deploy_again(self):
        command = ["deploy", "--source", "advanced", "--target", "leftbehind"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeployDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
