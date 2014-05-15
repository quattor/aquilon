#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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
"""Module for testing the add_static_route command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin


class TestAddStaticRoute(TestBrokerCommand, MachineTestMixin):

    def test_001_add_test_host(self):
        eth0_ip = self.net["unknown0"].usable[37]
        eth1_ip = self.net["routing1"].usable[1]
        self.create_host("unittest27.aqd-unittest.ms.com", eth0_ip, "ut3c5n9",
                         model="hs21-8853l5u", rack="ut3",
                         interfaces=["eth0", "eth1"], zebra=False,
                         eth0_mac=eth0_ip.mac,
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="unittest27-e1.aqd-unittest.ms.com",
                         personality="inventory")

    def test_100_add_route1(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.250.0", "--prefixlen", "23",
                   "--comments", "Route comments"]
        self.noouttest(command)

    def test_100_add_route1_personality(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", "inventory"]
        self.noouttest(command)

    def test_100_add_route2(self):
        gw = self.net["routing2"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.252.0", "--prefixlen", "23"]
        self.noouttest(command)

    def test_100_add_route2_guess(self):
        net = self.net["routing2"]
        command = ["add", "static", "route", "--networkip", net.ip,
                   "--ip", "192.168.254.0", "--prefixlen", "24"]
        out = self.statustest(command)
        self.matchoutput(out, "Gateway %s taken from default offset "
                         "1 for network %s." % (net.gateway, str(net)),
                         command)

    def test_100_add_route3(self):
        net = self.net["routing3"]
        ip = net[3]
        command = ["add", "static", "route", "--networkip", net.ip,
                   "--ip", "192.168.254.0", "--prefixlen", "24"]
        out = self.statustest(command)
        self.matchoutput(out, "Gateway %s taken from router address "
                         "of network %s." % (ip, str(net)), command)

    def test_110_add_overlap(self):
        net = self.net["routing2"]
        gw = net.usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.252.128", "--prefixlen", "25"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network %s already has an overlapping route to "
                         "192.168.252.0/23 using gateway %s." % (net.name, gw),
                         command)

    def test_120_add_default(self):
        gw = self.net["unknown0"].gateway
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "250.250.0.0", "--prefixlen", "16"]
        self.noouttest(command)

    def test_130_add_non_network_ip(self):
        gw = self.net["unknown0"].gateway
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.95.150", "--prefixlen", "24"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "192.168.95.150 is not a network address; "
                         "did you mean 192.168.95.0.",
                         command)

    def test_200_show_host(self):
        gw = self.net["routing1"].usable[-1]
        command = ["show", "host", "--hostname", "unittest26.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Static Route: 192.168.250.0/23 gateway %s" % gw,
                         command)
        self.matchoutput(out, "Comments: Route comments", command)
        self.matchclean(out, "192.168.252.0", command)

    def test_200_show_network(self):
        gw = self.net["routing1"].usable[-1]
        command = ["show", "network", "--ip", self.net["routing1"].ip]
        out = self.commandtest(command)
        self.matchoutput(out, "Static Route: 192.168.250.0/23 gateway %s" % gw,
                         command)
        self.matchoutput(out, "Comments: Route comments", command)
        self.matchclean(out, "192.168.252.0", command)

    def test_210_make_unittest26(self):
        command = ["make", "--hostname", "unittest26.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def test_220_verify_unittest26(self):
        eth0_net = self.net["unknown0"]
        eth0_ip = eth0_net.usable[23]
        eth1_net = self.net["routing1"]
        eth1_ip = eth1_net.usable[0]
        eth1_gw = eth1_net.usable[-1]
        command = ["cat", "--hostname", "unittest26.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest26.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (eth0_net.broadcast, eth0_net.gateway, eth0_ip,
                           eth0_net.netmask, eth0_net.gateway),
                          command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest26-e1.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "192.168.250.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.254.0"\s*\)\s*'
                          '\)\s*\)' %
                          (eth1_net.broadcast, eth1_net.gateway, eth1_ip,
                           eth1_net.netmask, eth1_gw),
                          command)

    def test_220_verify_unittest27(self):
        eth0_net = self.net["unknown0"]
        eth0_ip = eth0_net.usable[37]
        eth1_net = self.net["routing1"]
        eth1_ip = eth1_net.usable[1]
        eth1_gw = eth1_net.usable[-1]
        command = ["cat", "--hostname", "unittest27.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest27.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (eth0_net.broadcast, eth0_net.gateway, eth0_ip,
                           eth0_net.netmask, eth0_net.gateway),
                          command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest27-e1.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "192.168.248.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.255.0"\s*'
                          r'\),\s*'
                          r'nlist\(\s*'
                          r'"address", "192.168.250.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.254.0"\s*'
                          r'\)\s*\)\s*\)' %
                          (eth1_net.broadcast, eth1_net.gateway, eth1_ip,
                           eth1_net.netmask, eth1_gw, eth1_gw),
                          command)

    def test_230_verify_show_unittest02(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Static Route: 250.250.0.0/16 gateway %s" %
                         self.net["unknown0"].gateway, command)

    def test_240_verify_cat_unittest02(self):
        net = self.net["unknown0"]
        eth0_ip = net.usable[0]
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest02.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (net.broadcast, net.gateway,
                           eth0_ip, net.netmask, net.gateway),
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddStaticRoute)
    unittest.TextTestRunner(verbosity=2).run(suite)
