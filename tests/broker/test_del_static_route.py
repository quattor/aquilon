#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the del_static_route command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin


class TestDelStaticRoute(TestBrokerCommand, MachineTestMixin):

    def testdelroute1(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.250.0", "--prefixlen", "23"]
        self.noouttest(command)

    def testdelroute1again(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.250.0", "--prefixlen", "23"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Static Route to 192.168.250.0/23 using gateway "
                         "%s not found." % gw,
                         command)

    def testdelroute1_personality(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", "inventory"]
        self.noouttest(command)

    def testdelroute2(self):
        gw = self.net["routing2"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.252.0", "--prefixlen", "23"]
        self.noouttest(command)

    def testdelroute2_guess(self):
        gw = self.net["routing2"].gateway
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.254.0", "--prefixlen", "24"]
        self.noouttest(command)

    def testdelroute3(self):
        net = self.net["routing3"]
        gw = net[3]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.254.0", "--prefixlen", "24"]
        self.noouttest(command)

    def testdelroute4(self):
        gw = self.net["unknown0"].gateway
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "250.250.0.0", "--prefixlen", "16"]
        self.noouttest(command)

    def testverifynetwork(self):
        command = ["show", "network", "--ip", self.net["routing1"].ip]
        out = self.commandtest(command)
        self.matchclean(out, "Static Route", command)

    def testverifyunittest02(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Static Route", command)

    def testverifyunittest26(self):
        net = self.net["routing1"]
        ip = net.usable[0]
        command = ["cat", "--hostname", "unittest26.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth1" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest26-e1.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\)' %
                          (net.broadcast, net.gateway, ip, net.netmask),
                          command)

    def testdelunittest27(self):
        eth0_ip = self.net["unknown0"].usable[37]
        eth1_ip = self.net["routing1"].usable[1]
        self.delete_host("unittest27.aqd-unittest.ms.com", eth0_ip, "ut3c5n9",
                         interfaces=["eth0", "eth1"],
                         eth1_ip=eth1_ip)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelStaticRoute)
    unittest.TextTestRunner(verbosity=2).run(suite)
