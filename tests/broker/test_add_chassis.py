#!/usr/bin/env python2.6
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
"""Module for testing the add chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from chassistest import VerifyChassisMixin


class TestAddChassis(TestBrokerCommand, VerifyChassisMixin):

    def testaddut3c5(self):
        command = ["add", "chassis", "--chassis", "ut3c5.aqd-unittest.ms.com",
                   "--rack", "np3", "--model", "utchassis",
                   "--serial", "ABC1234", "--comments", "Some chassis comments"]
        self.noouttest(command)

    def testverifyaddut3c5(self):
        self.verifychassis("ut3c5.aqd-unittest.ms.com", "aurora_vendor",
                           "utchassis", "np3", "a", "3", "ABC1234",
                           comments="Some chassis comments")

    def testaddut3c1(self):
        command = "add chassis --chassis ut3c1.aqd-unittest.ms.com --rack ut3 --model utchassis"
        self.noouttest(command.split(" "))

    def testverifyaddut3c1(self):
        self.verifychassis("ut3c1.aqd-unittest.ms.com",
                           "aurora_vendor", "utchassis", "ut3", "a", "3")

    def testverifychassisdns(self):
        command = "search dns --fqdn ut3c1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)

    def testaddut9chassis(self):
        for i in range(1, 6):
            ip = self.net.unknown[10].usable[i]
            self.dsdb_expect_add("ut9c%d.aqd-unittest.ms.com" % i,
                                 ip, "oa", ip.mac)
            command = ["add", "chassis",
                       "--chassis", "ut9c%d.aqd-unittest.ms.com" % i,
                       "--rack", "ut9", "--model", "c-class",
                       "--ip", ip, "--mac", ip.mac, "--interface", "oa"]
            self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddut9chassis(self):
        for i in range(1, 6):
            self.verifychassis("ut9c%d.aqd-unittest.ms.com" % i,
                               "hp", "c-class", "ut9", "", "",
                               ip=str(self.net.unknown[10].usable[i]),
                               mac=self.net.unknown[10].usable[i].mac,
                               interface="oa")

    def testverifychassisall(self):
        command = ["show", "chassis", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Chassis: ut3c5", command)
        self.matchoutput(out, "Chassis: ut3c1", command)
        self.matchoutput(out, "Chassis: ut9c1", command)

    def testrejectbadlabelimplicit(self):
        command = ["add", "chassis", "--chassis", "not-alnum.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "utchassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not deduce a valid hardware label",
                         command)

    def testrejectbadlabelexplicit(self):
        command = ["add", "chassis", "--chassis", "ut3c6.aqd-unittest.ms.com",
                   "--label", "not-alnum", "--rack", "ut3", "--model", "utchassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal hardware label format 'not-alnum'.",
                         command)

    def testprimaryreuse(self):
        command = ["add", "chassis", "--chassis",
                   "ut3gd1r01.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "utchassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record ut3gd1r01.aqd-unittest.ms.com is already "
                         "used as the primary name of switch ut3gd1r01.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
