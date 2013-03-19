#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the add_router command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRouter(TestBrokerCommand):

    def testaddrouter(self):
        net = self.net.tor_net[6]
        command = ["add", "router", "--ip", net.gateway,
                   "--fqdn", "ut3gd1r04-v109-hsrp.aqd-unittest.ms.com",
                   "--building", "ut", "--comments", "Test router"]
        self.noouttest(command)

    def testaddrouteragain(self):
        net = self.net.tor_net[6]
        command = ["add", "router", "--ip", net.gateway,
                   "--fqdn", "ut3gd1r04-v110-hsrp.aqd-unittest.ms.com",
                   "--building", "ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is already present as a router "
                         "for network %s." % (net.gateway, net.ip), command)

    def testaddnormalhostasrouter(self):
        net = self.net.unknown[2]
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
        net = self.net.tor_net[0]
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
        for net_idx in range(0, 2):
            net = self.net.unknown[11 + net_idx]
            for rtr_idx in range(0, 2):
                rtr = "ut3gd1r0%d-v%d-hsrp.aqd-unittest.ms.com" % (net_idx + 1,
                                                                   rtr_idx + 109)
                command = ["add", "router", "--ip", net[rtr_idx + 1],
                           "--fqdn", rtr]
                self.noouttest(command)

    def testaddvplsrouters(self):
        net = self.net.vpls[0]
        self.noouttest(["add", "router", "--ip", net[1], "--building", "ut",
                        "--fqdn", "utvplsgw.aqd-unittest.ms.com"])
        self.noouttest(["add", "router", "--ip", net[2], "--building", "np",
                        "--fqdn", "npvplsgw.aqd-unittest.ms.com"])

    def testshowrouter(self):
        net = self.net.tor_net[6]
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
        net = self.net.tor_net[6]
        command = ["show", "network", "--ip", net.ip]
        out = self.commandtest(command)
        self.matchoutput(out, "Routers: %s (Building ut)" % net.gateway, command)

    def testshowbadip(self):
        ip = self.net.tor_net[0].gateway
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
        net = self.net.unknown[0].subnet()[0]
        # Test a different address assignment convention: router addresses are
        # at the end, not at the beginning
        command = ["add", "router", "--ip", net[-2],
                   "--fqdn", "gw1.excx.aqd-unittest.ms.com",
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testaddutcolo(self):
        net = self.net.unknown[1]
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
