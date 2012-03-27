#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011,2012  Contributor
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
"""Module for testing the search network command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestSearchNetwork(TestBrokerCommand):

    def testname(self):
        command = ["search_network", "--network=%s" % self.net.tor_net[0].ip]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.tor_net[0]), command)

    def testip0(self):
        command = ["search_network", "--ip=%s" % self.net.tor_net[0].ip]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.tor_net[0]), command)

    def testipcontains(self):
        command = ["search_network", "--ip=%s" % self.net.tor_net[0].usable[0]]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.tor_net[0]), command)

    def testtype(self):
        command = ["search_network", "--type=tor_net"]
        out = self.commandtest(command)
        for tor_net in self.net.tor_net:
            self.matchoutput(out, str(tor_net), command)
        for tor_net2 in self.net.tor_net2:
            self.matchclean(out, str(tor_net2), command)

    def testphysicalmachine(self):
        # unittest15.aqd-unittest.ms.com
        command = ["search_network", "--machine=ut8s02p1"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.tor_net[0]), command)

    # The test for virtual machines (with port groups) lives in
    # test_add_10gig_hardware.

    def testfailphysicalmachine(self):
        """This physical machine has no interface."""
        command = ["search_network", "--machine=ut3c1n9"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine ut3c1n9 has no interfaces assigned to a "
                         "network.",
                         command)

    # Failure for a virtual machine with no interface is in
    # test_add_10gig_hardware

    def testclusterpg(self):
        command = ["search_network", "--cluster=utecl5", "--pg=user-v710"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.unknown[2]), command)

    def testcluster(self):
        command = ["search_network", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.tor_net[2]), command)

    def testfqdn(self):
        command = ["search_network", "--fqdn=unittest15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net.tor_net[0]), command)

    def testlocation(self):
        command = ["search_network", "--building=ut"]
        out = self.commandtest(command)
        for net in self.net.all:
            self.matchoutput(out, str(net), command)

    def testfullinfo(self):
        command = ["search_network", "--ip=%s" % self.net.tor_net[0].ip,
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: %s" % self.net.tor_net[0].ip, command)
        self.matchoutput(out, "IP: %s" % self.net.tor_net[0].ip, command)

    def testnoenv(self):
        # Same IP defined differently in different environments
        net = self.net.unknown[0]
        command = ["search", "network", "--ip", net.ip, "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: %s" % net.ip, command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchclean(out, "Network Environment: excx", command)
        self.matchclean(out, "Network Environment: utcolo", command)
        self.matchoutput(out, "Netmask: %s" % net.netmask, command)
        self.matchclean(out, "excx-net", command)

    def testwithenv(self):
        # Same IP defined differently in different environments
        net = self.net.unknown[0]
        subnet = net.subnet()[0]
        command = ["search", "network", "--ip", net.ip,
                   "--network_environment", "excx", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: excx-net" % net.ip, command)
        self.matchclean(out, "Network: %s" % net.ip, command)
        self.matchoutput(out, "Network Environment: excx", command)
        self.matchclean(out, "Network Environment: internal", command)
        self.matchclean(out, "Network Environment: utcolo", command)
        self.matchoutput(out, "Netmask: %s" % subnet.netmask, command)
        self.matchclean(out, "Netmask: %s" % net.netmask, command)

    def testdynrange(self):
        command = ["search", "network", "--has_dynamic_ranges"]
        out = self.commandtest(command)
        expect = [self.net.tor_net2[0], self.net.tor_net2[1],
                  self.net.tor_net2[5]]
        for net in self.net.all:
            if net in expect:
                self.matchoutput(out, str(net), command)
            else:
                self.matchclean(out, str(net), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
