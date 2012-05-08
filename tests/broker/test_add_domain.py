#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Module for testing the add domain command."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddDomain(TestBrokerCommand):

    def test_000_fixprod(self):
        proddir = os.path.join(self.config.get("broker", "domainsdir"), "prod")
        if not os.path.exists(proddir):
            kingdir = self.config.get("broker", "kingdir")
            self.gitcommand(["clone", kingdir, proddir])

    def test_000_fixnyprod(self):
        kingdir = self.config.get("broker", "kingdir")
        (out, err) = self.gitcommand(["branch"], cwd=kingdir)
        if out.find("ny-prod") < 0:
            self.gitcommand(["branch", "--track", "ny-prod", "prod"],
                            cwd=kingdir)
        nydir = os.path.join(self.config.get("broker", "domainsdir"),
                             "ny-prod")
        if not os.path.exists(nydir):
            self.gitcommand(["clone", kingdir, nydir])

    def test_100_addunittest(self):
        command = ["add_domain", "--domain=unittest", "--track=utsandbox",
                   "--comments", "aqd unit test tracking domain",
                   "--disallow_manage"]
        self.successtest(command)
        self.failUnless(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "unittest")))

    def test_100_addutprod(self):
        command = ["add_domain", "--domain=ut-prod", "--track=prod"]
        self.successtest(command)
        self.failUnless(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "ut-prod")))

    def test_100_adddeployable(self):
        command = ["add_domain", "--domain=deployable", "--start=prod"]
        self.successtest(command)
        self.failUnless(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "deployable")))

    def test_100_invalidtrack(self):
        command = ["add_domain", "--domain=notvalid-prod", "--track=prod",
                   "--change_manager"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot enforce a change manager for tracking domain",
                         command)

    def test_100_nomanage(self):
        command = ["add_domain", "--domain", "nomanage"]
        self.successtest(command)

    def test_200_verifyunittest(self):
        command = ["show_domain", "--domain=unittest"]
        out = self.commandtest(command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Tracking: sandbox utsandbox", command)
        self.matchoutput(out, "Comments: aqd unit test tracking domain",
                         command)
        self.matchoutput(out, "May Contain Hosts/Clusters: False", command)

    def test_200_verifyutprod(self):
        command = ["show_domain", "--domain=ut-prod"]
        out = self.commandtest(command)
        self.matchoutput(out, "Domain: ut-prod", command)
        self.matchoutput(out, "Tracking: domain prod", command)

    def test_200_verifydeployable(self):
        command = ["show_domain", "--domain=deployable"]
        out = self.commandtest(command)
        self.matchoutput(out, "Domain: deployable", command)
        self.matchclean(out, "Tracking:", command)

    def test_200_verifynomanage(self):
        command = ["show_domain", "--domain=nomanage"]
        out = self.commandtest(command)
        self.matchoutput(out, "Domain: nomanage", command)
        self.matchoutput(out, "May Contain Hosts/Clusters: True", command)

    def test_210_verifysearchtrack(self):
        command = ["search", "domain", "--track", "utsandbox"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest", command)
        self.matchclean(out, "ut-prod", command)

    def test_210_verifysearchchm(self):
        command = ["search", "domain", "--change_manager"]
        self.noouttest(command)

    def test_210_verifysearchowner(self):
        user = self.config.get("unittest", "user")
        command = ["search", "domain", "--owner", user]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest", command)
        self.matchoutput(out, "prod", command)
        self.matchoutput(out, "ut-prod", command)
        self.matchoutput(out, "deployable", command)
        self.matchclean(out, "utsandbox", command)

    def test_900_verifyall(self):
        command = ["show_domain", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Domain: prod", command)
        self.matchoutput(out, "Domain: ut-prod", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Domain: deployable", command)
        self.matchclean(out, "Sandbox: utsandbox", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
