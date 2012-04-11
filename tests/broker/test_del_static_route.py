#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Module for testing the del_static_route command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelStaticRoute(TestBrokerCommand):

    def testdelroute1(self):
        gw = self.net.unknown[14].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.250.0", "--prefixlen", "23"]
        self.noouttest(command)

    def testdelroute1again(self):
        gw = self.net.unknown[14].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.250.0", "--prefixlen", "23"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Static Route to 192.168.250.0/23 using gateway "
                         "%s not found." % gw,
                         command)

    def testdelroute2(self):
        gw = self.net.unknown[15].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.252.0", "--prefixlen", "23"]
        self.noouttest(command)

    def testdelroute3(self):
        gw = self.net.unknown[0].gateway
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "250.250.0.0", "--prefixlen", "16"]
        self.noouttest(command)

    def testverifynetwork(self):
        command = ["show", "network", "--ip", self.net.unknown[14].ip]
        out = self.commandtest(command)
        self.matchclean(out, "Static Route", command)

    def testverifyunittest02(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Static Route", command)

    def testverifyunittest26(self):
        net = self.net.unknown[14]
        ip = net.usable[0]
        command = ["cat", "--hostname", "unittest26.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelStaticRoute)
    unittest.TextTestRunner(verbosity=2).run(suite)
