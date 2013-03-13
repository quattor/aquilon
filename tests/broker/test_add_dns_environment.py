#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the add dns environment command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddDnsEnvironment(TestBrokerCommand):

    def testaddutenv(self):
        command = ["add", "dns", "environment", "--dns_environment", "ut-env",
                   "--comment", "Unit test environment"]
        self.noouttest(command)

    def testaddexcx(self):
        command = ["add", "dns", "environment", "--dns_environment", "excx"]
        self.noouttest(command)

    def testaddutenvagain(self):
        command = ["add", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Environment ut-env already exists.", command)

    def testaddbadname(self):
        command = ["add", "dns", "environment", "--dns_environment", "<badname>"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'<badname>' is not a valid value for DNS environment",
                         command)

    def testshowenv(self):
        command = ["show", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Comments: Unit test environment", command)

    def testshowall(self):
        command = ["show", "dns", "environment", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out, "DNS Environment: external", command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Comments: Unit test environment", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDnsEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
