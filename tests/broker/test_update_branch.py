#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the update domain command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateBranch(TestBrokerCommand):
    # FIXME: Add some tests around (no)autosync
    # FIXME: Verify against sandboxes

    def testupdatedomain(self):
        self.noouttest(["update", "domain", "--domain", "deployable",
                        "--comments", "Updated Comments",
                        "--compiler_version=8.2.7"])

    def testverifyupdatedomain(self):
        command = "show domain --domain deployable"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: deployable", command)
        self.matchoutput(out,
                         "Compiler: "
                         "/ms/dist/elfms/PROJ/panc/8.2.7/lib/panc.jar",
                         command)
        self.matchoutput(out, "Comments: Updated Comments", command)

    def testbadcompilerversioncharacters(self):
        command = ["update_sandbox", "--sandbox=changetest1",
                   "--compiler_version=version!with@bad#characters"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid characters in compiler version",
                         command)

    def testbadcompilerversion(self):
        command = ["update_sandbox", "--sandbox=changetest1",
                   "--compiler_version=version-does-not-exist"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Compiler not found at", command)

    def testnotadomain(self):
        command = ["update_domain", "--domain=changetest1", "--change_manager"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Domain changetest1 not found.", command)

    def testnotasandbox(self):
        command = ["update_sandbox", "--sandbox=unittest", "--autosync"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Sandbox unittest not found.", command)

    def testchangemanagerfortracked(self):
        command = ["update_domain", "--domain=ut-prod", "--change_manager"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot enforce a change manager for tracking "
                         "domains.",
                         command)

    def testupdateprod(self):
        self.noouttest(["update", "domain", "--domain", "prod",
                        "--change_manager"])

    def testverifyprod(self):
        command = ["show", "domain", "--domain", "prod"]
        out = self.commandtest(command)
        self.matchoutput(out, "Requires Change Manager: True", command)

    def testupdateunittest(self):
        self.noouttest(["update", "domain", "--domain", "unittest",
                        "--allow_manage"])

    def testverifyunittest(self):
        command = ["show", "domain", "--domain", "unittest"]
        out = self.commandtest(command)
        self.matchoutput(out, "May Contain Hosts/Clusters: True", command)

    def testupdatenomanage(self):
        command = ["update", "domain", "--domain", "nomanage",
                   "--disallow_manage"]
        self.noouttest(command)

    def testverifynomanage(self):
        command = ["show", "domain", "--domain", "nomanage"]
        out = self.commandtest(command)
        self.matchoutput(out, "May Contain Hosts/Clusters: False", command)

    def testverifysearchchm(self):
        command = ["search", "domain", "--change_manager"]
        out = self.commandtest(command)
        self.matchoutput(out, "prod", command)
        self.matchclean(out, "ut-prod", command)
        self.matchclean(out, "deployable", command)

    def testverifysearchversion(self):
        command = ["search", "domain", "--compiler_version", "8.2.7"]
        out = self.commandtest(command)
        self.matchclean(out, "prod", command)
        self.matchclean(out, "ut-prod", command)
        self.matchoutput(out, "deployable", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateBranch)
    unittest.TextTestRunner(verbosity=2).run(suite)
