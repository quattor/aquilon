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
"""Module for testing the behavior of network environments."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateNetworkEnvironment(TestBrokerCommand):

    def testdelexcx(self):
        command = ["del", "network", "environment",
                   "--network_environment", "excx"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network Environment excx still has networks defined, "
                         "delete them first.",
                         command)

    def testupdatelocation(self):
        command = ["update", "network", "environment",
                   "--network_environment", "utcolo",
                   "--building", "ut"]
        self.noouttest(command)

    def testclearlocation(self):
        command = ["update", "network", "environment",
                   "--network_environment", "excx",
                   "--clear_location"]
        self.noouttest(command)

    def testverifyexcx(self):
        command = ["show", "network", "environment",
                   "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Environment: excx", command)
        self.matchclean(out, "Building:", command)
        self.matchoutput(out, "Comments: Exchange X", command)

    def testverifyutcolo(self):
        command = ["show", "network", "environment",
                   "--network_environment", "utcolo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Environment: utcolo", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Comments: Unit test colo environment", command)

    def testverifysearch(self):
        command = ["search", "network", "environment",
                   "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Environment: utcolo", command)
        self.matchclean(out, "excx", command)
        self.matchclean(out, "internal", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateNetworkEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
