#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014  Contributor
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
"""Module for testing constraints in commands involving domain."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDomainConstraints(TestBrokerCommand):

    def testdelsandboxwithhost(self):
        command = "del sandbox --sandbox utsandbox"
        self.badrequesttest(command.split(" "))
        # This wouldn't get deleted anyway, but doesn't hurt to verify.
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.assert_(os.path.exists(sandboxdir))

    def testverifydelsandboxwithhostfailed(self):
        command = "show sandbox --sandbox utsandbox"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: utsandbox", command)

    def testdeldomainwithhost(self):
        command = "del domain --domain ny-prod"
        self.badrequesttest(command.split(" "))
        domainsdir = self.config.get("broker", "domainsdir")
        self.assert_(os.path.exists(os.path.join(domainsdir, "ny-prod")))

    def testverifydeldomainwithhostfailed(self):
        command = "show domain --domain ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: ny-prod", command)

    def testupdatedomainformat(self):
        command = ["update_domain", "--domain", "unittest",
                   "--profile_formats", "json"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Domain unittest has compileable objects, "
                         "the profile format cannot be changed.", command)

    def testupdatesandboxformat(self):
        command = ["update_sandbox", "--sandbox", "utsandbox",
                   "--profile_formats", "json"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Sandbox utsandbox has compileable objects, "
                         "the profile format cannot be changed.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDomainConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
