#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

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

    def testdelserviceaddress(self):
        command = ["del", "interface", "--interface", "eth1",
                   "--machine", "ut3c5n2"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Public Interface eth1 of machine "
                         "unittest20.aqd-unittest.ms.com still has the "
                         "following service addresses bound to it, delete "
                         "them first: hostname, zebra2, zebra3.",
                         command)

    def testpgmismatchphys(self):
        # If
        # - the machine has a host defined,
        # - the host is in a cluster,
        # - and the cluster has a switch,
        # then setting an invalid port group is an error.
        # TODO: why is this not an error if the above conditions do not hold?
        command = ["add", "interface", "--machine", "evh51.aqd-unittest.ms.com",
                   "--interface", "eth2", "--pg", "unused-v999"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Switch ut01ga2s01.aqd-unittest.ms.com does not have "
                         "port group unused-v999 assigned.",
                         command)

    def testpgmismatchvm(self):
        command = ["add", "interface", "--machine", "ivirt1.aqd-unittest.ms.com",
                   "--interface", "eth1", "--pg", "unused-v999"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot verify port group availability: no record "
                         "for VLAN 999 on switch ut01ga2s01.aqd-unittest.ms.com.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInterfaceConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
