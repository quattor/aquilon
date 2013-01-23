#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the deploy domain command."""


import os
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
        domainsdir = self.config.get("broker", "domainsdir")
        ddir = os.path.join(domainsdir, "deployable")
        template = os.path.join(ddir, "aquilon", "archetype", "base.tpl")
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
        domainsdir = self.config.get("broker", "domainsdir")
        # The change should be in prod...
        ddir = os.path.join(domainsdir, "prod")
        template = os.path.join(ddir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")
        # ...but not in the ut-prod tracking domain.
        ddir = os.path.join(domainsdir, "ut-prod")
        template = os.path.join(ddir, "aquilon", "archetype", "base.tpl")
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeployDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
