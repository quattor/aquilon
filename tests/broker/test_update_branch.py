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
"""Module for testing the update domain command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
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
        compiler = self.config.get("panc", "pan_compiler", raw=True) % {
            'version': '8.2.7'}
        self.matchoutput(out, "Compiler: %s" % compiler,
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
