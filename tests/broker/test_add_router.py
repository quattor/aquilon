#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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
"""Module for testing the add_router command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRouter(TestBrokerCommand):

    def testaddrouter(self):
        net = self.net["verari_eth1"]
        command = ["add", "router", "--ip", net.gateway,
                   "--fqdn", "ut3gd1r04-v109-hsrp.aqd-unittest.ms.com",
                   "--building", "ut", "--comments", "Test router"]
        self.noouttest(command)

    def testaddrouteragain(self):
        net = self.net["verari_eth1"]
        command = ["add", "router", "--ip", net.gateway,
                   "--fqdn", "ut3gd1r04-v110-hsrp.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is already present as a router "
                         "for network %s." % (net.gateway, net.ip), command)

    def testaddnormalhostasrouter(self):
        net = self.net["ut01ga2s01_v710"]
        ip = net.usable[0]
        command = ["add", "router", "--ip", ip,
                   "--fqdn", "not-a-router.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is not a valid router address on "
                         "network %s." % (ip, net.ip),
                         command)

    def testaddreserved(self):
        net = self.net["tor_net_0"]
        ip = net.reserved[0]
        command = ["add", "router", "--ip", ip,
                   "--fqdn", "reserved-address.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is not a valid router address on "
                         "network %s." % (ip, net.ip),
                         command)

    def testaddzebrarouters(self):
        for net_idx, net in enumerate((self.net["zebra_eth0"],
                                       self.net["zebra_eth1"])):
            for rtr_idx in range(0, 2):
                rtr = "ut3gd1r0%d-v%d-hsrp.aqd-unittest.ms.com" % (net_idx + 1,
                                                                   rtr_idx + 109)
                command = ["add", "router", "--ip", net[rtr_idx + 1],
                           "--fqdn", rtr]
                self.noouttest(command)

    def testaddvplsrouters(self):
        net = self.net["vpls"]
        self.noouttest(["add", "router", "--ip", net[1], "--building", "ut",
                        "--fqdn", "utvplsgw.aqd-unittest.ms.com"])
        self.noouttest(["add", "router", "--ip", net[2], "--building", "np",
                        "--fqdn", "npvplsgw.aqd-unittest.ms.com"])

    def testshowrouter(self):
        net = self.net["verari_eth1"]
        command = ["show", "router", "--ip", net.gateway]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Router: ut3gd1r04-v109-hsrp.aqd-unittest.ms.com [%s]"
                         % net.gateway,
                         command)
        self.matchoutput(out, "Network: %s [%s]" % (net.ip, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Comments: Test router", command)

    def testshownetwork(self):
        net = self.net["verari_eth1"]
        command = ["show", "network", "--ip", net.ip]
        out = self.commandtest(command)
        self.matchoutput(out, "Routers: %s (Building ut)" % net.gateway, command)

    def testshowbadip(self):
        ip = self.net["tor_net_0"].gateway
        command = ["show", "router", "--ip", ip]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Router with IP address %s not found." % ip,
                         command)

    def testshownotarouter(self):
        command = ["show", "router",
                   "--fqdn", "arecord13.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Router named arecord13.aqd-unittest.ms.com not found.",
                         command)

    def testshowrouterall(self):
        command = ["show", "router", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Router: ut3gd1r01-v109-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r01-v110-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r02-v109-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r02-v110-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Router: ut3gd1r04-v109-hsrp.aqd-unittest.ms.com", command)
        self.matchclean(out, "excx", command)
        self.matchclean(out, "utcolo", command)

    def testaddexcx(self):
        net = self.net["unknown0"].subnet()[0]
        # Test a different address assignment convention: router addresses are
        # at the end, not at the beginning
        command = ["add", "router", "--ip", net[-2],
                   "--fqdn", "gw1.excx.aqd-unittest.ms.com",
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testaddutcolo(self):
        net = self.net["unknown1"]
        command = ["add", "router", "--ip", net[2],
                   "--fqdn", "gw1.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def testshowexcx(self):
        command = ["show", "router", "--network_environment", "excx", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Router: gw1.excx.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r01", command)
        self.matchclean(out, "ut3gd1r02", command)
        self.matchclean(out, "ut3gd1r04", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRouter)
    unittest.TextTestRunner(verbosity=2).run(suite)
