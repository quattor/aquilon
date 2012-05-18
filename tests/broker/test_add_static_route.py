#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Module for testing the add_static_route command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddStaticRoute(TestBrokerCommand):

    def test_100_add_route1(self):
        gw = self.net.unknown[14].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.250.0", "--prefixlen", "23",
                   "--comments", "Route comments"]
        self.noouttest(command)

    def test_100_add_route2(self):
        gw = self.net.unknown[15].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.252.0", "--prefixlen", "23"]
        self.noouttest(command)

    def test_110_add_overlap(self):
        net = self.net.unknown[15]
        gw = net.usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.252.128", "--prefixlen", "25"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network %s already has an overlapping route to "
                         "192.168.252.0/23 using gateway %s." % (net.ip, gw),
                         command)

    def test_120_add_default(self):
        gw = self.net.unknown[0].gateway
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "250.250.0.0", "--prefixlen", "16"]
        self.noouttest(command)

    def test_200_show_host(self):
        gw = self.net.unknown[14].usable[-1]
        command = ["show", "host", "--hostname", "unittest26.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Static Route: 192.168.250.0/23 gateway %s" % gw,
                         command)
        self.matchoutput(out, "Comments: Route comments", command)
        self.matchclean(out, "192.168.252.0", command)

    def test_200_show_network(self):
        gw = self.net.unknown[14].usable[-1]
        command = ["show", "network", "--ip", self.net.unknown[14].ip]
        out = self.commandtest(command)
        self.matchoutput(out, "Static Route: 192.168.250.0/23 gateway %s" % gw,
                         command)
        self.matchoutput(out, "Comments: Route comments", command)
        self.matchclean(out, "192.168.252.0", command)

    def test_210_make_unittest26(self):
        command = ["make", "--hostname", "unittest26.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 compiled", command)

    def test_220_verify_unittest26(self):
        eth0_net = self.net.unknown[0]
        eth0_ip = eth0_net.usable[23]
        eth1_net = self.net.unknown[14]
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
                          r'"network_type", "unknown"\s*\)' %
                          (eth0_net.broadcast, eth0_net.gateway, eth0_ip,
                           eth0_net.netmask),
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

    def test_230_verify_show_unittest02(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Static Route: 250.250.0.0/16 gateway %s" %
                         self.net.unknown[0].gateway, command)

    def test_240_verify_cat_unittest02(self):
        net = self.net.unknown[0]
        eth0ip = net.usable[0]
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # No routes should be listed here, because the gw is the default gw
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest02.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\)\s*' %
                          (net.broadcast, net.gateway,
                           eth0ip, net.netmask),
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddStaticRoute)
    unittest.TextTestRunner(verbosity=2).run(suite)
