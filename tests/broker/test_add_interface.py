#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Module for testing the add interface command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddInterface(TestBrokerCommand):

    def testaddut3c5n10eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3c5n10", "--mac", self.hostmac0.upper()])

    def testaddut3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "ut3c5n10", "--mac", self.hostmac1.lower()])

    def testverifyaddut3c5n10interfaces(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                self.hostmac0.lower(), command)
        self.matchoutput(out, "Interface: eth1 %s boot=False" %
                self.hostmac1.lower(), command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac0.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "%s";""" % self.hostmac1.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth1/boot" = true;""",
                command)

    def testaddut3c1n3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3c1n3", "--mac", self.hostmac2.upper()])

    def testaddut3c1n3eth1(self):
        testmac = []
        for i in self.hostmac3.split(":"):
            if i.startswith("0"):
                testmac.append(i[1])
            else:
                testmac.append(i)
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "ut3c1n3", "--mac", ":".join(testmac)])

    def testaddut3c1n3bmc(self):
        self.noouttest(["add", "interface", "--interface", "bmc",
            "--machine", "ut3c1n3", "--mac", self.hostmac10.lower()])

    def testverifyaddut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac2.lower(), command)
        self.matchoutput(out, "Interface: eth1 %s boot=False" %
                         self.hostmac3.lower(), command)
        self.matchoutput(out, "Interface: bmc %s boot=False" %
                         self.hostmac10.lower(), command)

    def testverifyshowmanagermissing(self):
        command = "show manager --missing"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            "# No host found for machine ut3c1n3 with management interface",
            command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac2.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "%s";""" % self.hostmac3.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth1/boot" = true;""",
                command)
        self.matchoutput(out, """"console/bmc" = nlist(""", command)
        self.matchoutput(out, '"hwaddr", "%s"' % self.hostmac10.lower(),
                         command)

    def testaddut3c1n4eth0(self):
        testmac = "".join(self.hostmac4.split(":"))
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3c1n4", "--mac", testmac])

    def testfailaddut3c1n4eth1(self):
        # Mac in use by a chassis, below.
        command = ["add", "interface", "--interface", "eth1",
                   "--mac", self.hostmac8, "--machine", "ut3c1n4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Mac '%s' already in use: " % self.hostmac8,
                         command)

    def testverifyaddut3c1n4interface(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac4.lower(), command)
        self.matchclean(out, "Interface: eth1", command)

    def testverifycatut3c1n4interface(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac4.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)

    def testaddinterfaceut3c5(self):
        command = ["add", "interface", "--interface", "oa",
                   "--mac", self.hostmac8, "--ip", self.hostip8,
                   "--chassis", "ut3c5.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifyaddinterfaceut3c5(self):
        command = "show chassis --chassis ut3c5.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Chassis: ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip8, command)
        self.matchoutput(out, "Interface: oa %s boot=False" %
                         self.hostmac8, command)
        self.matchclean(out, "Interface: oa2", command)

    def testfailaddinterfaceut3c1(self):
        command = ["add", "interface", "--interface", "oa",
                   "--mac", self.hostmac8, "--ip", self.hostip8,
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Mac '%s' already in use: " % self.hostmac8,
                         command)

    def testverifyfailaddinterfaceut3c1(self):
        command = "show chassis --chassis ut3c1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchclean(out, "Interface: oa", command)

    def testaddinterfacenp997gd1r04(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--mac", self.hostmac9, "--ip", self.hostip9,
                   "--tor_switch", "np997gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifyaddinterfacenp997gd1r04(self):
        command = "show tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Tor_switch: np997gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip9, command)
        self.matchoutput(out, "Interface: xge49 %s boot=False" %
                         self.hostmac9, command)
        self.matchclean(out, "Interface: xge50", command)

    def testfailaddinterfaceut3dg1r01(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--mac", self.hostmac9, "--ip", self.hostip9,
                   "--tor_switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Mac '%s' already in use: " % self.hostmac9,
                         command)

    def testverifyfailaddinterfaceut3dg1r01(self):
        command = "show tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Tor_switch: ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchclean(out, "Interface: xge49", command)

    # These two will eventually be created when testing the addition
    # of a whole rack of machines based on a CheckNet sweep.
    def testaddut3s01p1aeth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3s01p1a", "--mac", self.hostmac12])

    def testverifyaddut3s01p1aeth0(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac12.lower(), command)

    def testaddut3s01p1beth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3s01p1b", "--mac", self.hostmac13])

    def testverifyaddut3s01p1beth0(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac13.lower(), command)

    def testaddut8s02p1eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut8s02p1", "--mac", self.hostmac15])

    def testverifyaddut8s02p1eth0(self):
        command = "show machine --machine ut8s02p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac15.lower(), command)

    def testaddut8s02p2eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut8s02p2", "--mac", self.hostmac16])

    def testverifyaddut8s02p2eth0(self):
        command = "show machine --machine ut8s02p2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac16.lower(), command)

    def testaddut8s02p3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut8s02p3", "--mac", self.hostmac17])

    def testverifyaddut8s02p3eth0(self):
        command = "show machine --machine ut8s02p3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac17.lower(), command)

    def testaddhprackinterfaces(self):
        for i in range(51, 100):
            hostmac = getattr(self, "hostmac%d" % i)
            port = i - 50
            machine = "ut9s03p%d" % port
            self.noouttest(["add", "interface", "--interface", "eth0",
                            "--machine", machine, "--mac", hostmac])

    def testaddverarirackinterfaces(self):
        for i in range(101, 150):
            hostmac = getattr(self, "hostmac%d" % i)
            port = i - 100
            machine = "ut10s04p%d" % port
            self.noouttest(["add", "interface", "--interface", "eth0",
                            "--machine", machine, "--mac", hostmac])


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

