#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the add_router_address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRouterAddress(TestBrokerCommand):

    def test_100_add_router(self):
        net = self.net["ut10_eth1"]
        command = ["add", "router", "address", "--ip", net.gateway,
                   "--fqdn", "ut3gd1r04-v109-hsrp.aqd-unittest.ms.com",
                   "--building", "ut",
                   "--comments", "Some router address comments"]
        self.noouttest(command)

    def test_101_add_router_primary_address(self):
        primary_name = "ut3gd1r04.aqd-unittest.ms.com"
        command = ["add", "router", "address",
                   "--fqdn", primary_name]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "{0} is already used as the primary name of switch "
                         "ut3gd1r04.".format(primary_name),
                         command)

    def test_105_show_router(self):
        net = self.net["ut10_eth1"]
        command = ["show", "router", "address", "--ip", net.gateway]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Router: ut3gd1r04-v109-hsrp.aqd-unittest.ms.com [%s]"
                         % net.gateway,
                         command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Comments: Some router address comments", command)

    def test_105_show_network(self):
        net = self.net["ut10_eth1"]
        command = ["show", "network", "--ip", net.ip]
        out = self.commandtest(command)
        self.matchoutput(out, "Routers: %s (Building ut)" % net.gateway, command)

    def test_105_show_network_proto(self):
        net = self.net["ut10_eth1"]
        command = ["show", "network", "--ip", net.ip, "--format", "proto"]
        netmsg = self.protobuftest(command)[0]
        self.assertEqual(len(netmsg.routers), 1)
        self.assertEqual(netmsg.routers[0], str(net.gateway))

    def test_110_add_default_router(self):
        net = self.net["routing3"]
        ip = net[3]
        command = ["add", "router", "address", "--ip", ip,
                   "--fqdn", "ut3gd1r01-v111-hsrp.aqd-unittest.ms.com",
                   "--building", "ut",
                   "--comments", "Some other router address comments"]
        self.noouttest(command)

    def test_120_add_zebra_routers(self):
        for net_idx, net in enumerate((self.net["zebra_eth0"],
                                       self.net["zebra_eth1"])):
            for rtr_idx in range(0, 2):
                rtr = "ut3gd1r0%d-v%d-hsrp.aqd-unittest.ms.com" % (net_idx + 1,
                                                                   rtr_idx + 109)
                command = ["add", "router", "address", "--ip", net[rtr_idx + 1],
                           "--fqdn", rtr]
                self.noouttest(command)

    def test_125_show_zebra0_proto(self):
        net = self.net["zebra_eth0"]
        command = ["show", "network", "--ip", net.ip, "--format", "proto"]
        netmsg = self.protobuftest(command)[0]
        self.assertEqual(len(netmsg.routers), 2)
        self.assertEqual(set(netmsg.routers), set([str(net[1]), str(net[2])]))

    def test_130_add_vpls_routers(self):
        net = self.net["vpls"]
        self.noouttest(["add", "router", "address", "--ip", net[1], "--building", "ut",
                        "--fqdn", "utvplsgw.aqd-unittest.ms.com"])
        self.noouttest(["add", "router", "address", "--ip", net[2], "--building", "np",
                        "--fqdn", "npvplsgw.aqd-unittest.ms.com"])

    def test_140_add_excx(self):
        net = list(self.net["unknown0"].subnets())[0]
        # Test a different address assignment convention: router addresses are
        # at the end, not at the beginning
        command = ["add", "router", "address", "--ip", net[-2],
                   "--fqdn", "gw1.excx.aqd-unittest.ms.com",
                   "--network_environment", "excx"]
        self.noouttest(command)

    def test_145_show_excx(self):
        command = ["show", "router", "address", "--network_environment", "excx", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Router: gw1.excx.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r01", command)
        self.matchclean(out, "ut3gd1r02", command)
        self.matchclean(out, "ut3gd1r04", command)

    def test_150_add_utcolo(self):
        net = self.net["unknown1"]
        command = ["add", "router", "address", "--ip", net[2],
                   "--fqdn", "gw1.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def test_200_add_router_again(self):
        net = self.net["ut10_eth1"]
        command = ["add", "router", "address", "--ip", net.gateway,
                   "--fqdn", "ut3gd1r04-v110-hsrp.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address {} is already in use by DNS "
                              "record ut3gd1r04-v109-hsrp.aqd-unittest.ms.com.".format(net.gateway),
                         command)

    def test_200_add_normal_host_as_router(self):
        net = self.net["ut01ga2s01_v710"]
        ip = net.usable[0]
        command = ["add", "router", "address", "--ip", ip,
                   "--fqdn", "not-a-router.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is not a valid router address on "
                         "network %s [%s]." % (ip, net.name, net),
                         command)

    def test_200_add_reserved(self):
        net = self.net["tor_net_0"]
        ip = net.reserved[0]
        command = ["add", "router", "address", "--ip", ip,
                   "--fqdn", "reserved-address.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The IP address {} is reserved for dynamic DHCP for "
                              "a switch on subnet {}".format(ip, net.network_address),
                         command)

    def test_200_show_bad_ip(self):
        ip = self.net["tor_net_0"].gateway
        command = ["show", "router", "address", "--ip", ip]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Router with IP address %s not found." % ip,
                         command)

    def test_200_show_not_a_router(self):
        command = ["show", "router", "address",
                   "--fqdn", "arecord13.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Router named arecord13.aqd-unittest.ms.com not found.",
                         command)

    def test_300_show_router_all(self):
        command = ["show", "router", "address", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Router: ut3gd1r01-v109-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r01-v110-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r02-v109-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r02-v110-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r04-v109-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r01-v111-hsrp.aqd-unittest.ms.com", command)
        self.matchclean(out, "excx", command)
        self.matchclean(out, "utcolo", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRouterAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
