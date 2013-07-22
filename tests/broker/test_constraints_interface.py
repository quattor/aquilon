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
"""Module for testing constraints in commands involving interfaces."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestInterfaceConstraints(TestBrokerCommand):

    def testdelinterfaceprimary(self):
        command = ["del", "interface", "--interface", "eth0",
                   "--machine", "ut3c1n3"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "holds the primary address", command)

    def testdelinterfacewithvlans(self):
        command = ["del", "interface", "--interface", "eth1",
                   "--machine", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is the parent of the following VLAN interfaces",
                         command)

    def testdelmasterwithslaves(self):
        command = ["del", "interface", "--interface", "bond0",
                   "--machine", "ut3c5n3"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is the master of the following slave interfaces",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInterfaceConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
