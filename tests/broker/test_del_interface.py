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
"""Module for testing the del interface command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelInterface(TestBrokerCommand):

    # Not testing del interface for ut3c5n10... testing that those
    # interfaces are removed automatically when the machine is removed.

    def testdelut3c1n3eth0(self):
        self.noouttest(["del", "interface", "--interface", "eth0",
                        "--machine", "ut3c1n3"])

    def testdelut3c1n3eth1(self):
        self.noouttest(["del", "interface",
                        "--mac", self.net["unknown0"].usable[3].mac.upper()])

    def testnotamachine(self):
        command = ["del", "interface", "--interface", "xge49",
                   "--machine", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a machine", command)

    def testnotaswitch(self):
        command = ["del", "interface", "--interface", "oa",
                   "--network_device", "ut3c5"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a switch", command)

    def testnotachassis(self):
        command = ["del", "interface", "--interface", "eth0",
                   "--chassis", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a chassis", command)

    def testverifydelut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth", command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "eth0", command)
        self.matchclean(out, "eth1", command)

    def testdelut3gd1r04vlan220(self):
        command = ["del", "interface", "--interface", "vlan220",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifydelut3gd1r04vlan220(self):
        command = ["show", "network_device", "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "vlan220", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)
