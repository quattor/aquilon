#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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

    def testaddut3c5n10eth0_good_mac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--mac", self.net.unknown[0].usable[0].mac.upper()])

    def testaddut3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n10",
                        "--mac", self.net.unknown[0].usable[1].mac.lower()])

    def testverifyaddut3c5n10interfaces(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.unknown[0].usable[0].mac.lower(),
                         command)
        self.matchoutput(out,
                         "Interface: eth1 %s boot=False" %
                         self.net.unknown[0].usable[1].mac.lower(),
                         command)
        self.matchclean(out, "Port Group", command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"boot", true,\s*\);'
                          % self.net.unknown[0].usable[0].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*\);'
                          % self.net.unknown[0].usable[1].mac,
                          command)

    def testaddut3c1n3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c1n3",
                        "--mac", self.net.unknown[0].usable[2].mac.upper()])

    def testaddut3c1n3eth1(self):
        testmac = []
        for i in self.net.unknown[0].usable[3].mac.split(":"):
            if i.startswith("0"):
                testmac.append(i[1])
            else:
                testmac.append(i)
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c1n3", "--mac", ":".join(testmac)])

    def testaddut3c1n3bmc(self):
        self.noouttest(["add", "interface", "--interface", "bmc",
                        "--machine", "ut3c1n3",
                        "--mac", self.net.unknown[0].usable[4].mac.lower()])

    def testverifyaddut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.unknown[0].usable[2].mac.lower(),
                         command)
        self.matchoutput(out,
                         "Interface: eth1 %s boot=False" %
                         self.net.unknown[0].usable[3].mac.lower(),
                         command)
        self.matchoutput(out,
                         "Interface: bmc %s boot=False" %
                         self.net.unknown[0].usable[4].mac.lower(),
                         command)

    def testverifyshowmanagermissing(self):
        command = "show manager --missing"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            "# No host found for machine ut3c1n3 with management interface",
            command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"boot", true,\s*\);'
                          % self.net.unknown[0].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*\);'
                          % self.net.unknown[0].usable[3].mac,
                          command)
        self.searchoutput(out,
                          r'"console/bmc" = nlist\(\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % (self.net.unknown[0].usable[4].mac.lower()),
                          command)

    def testaddut3c1n4eth0(self):
        testmac = "".join(self.net.unknown[0].usable[5].mac.split(":"))
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c1n4", "--mac", testmac])

    def testfailaddut3c1n4eth1(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--machine", "ut3c1n4",
                   "--mac", self.net.unknown[0].usable[0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Mac '%s' already in use: " %
                         self.net.unknown[0].usable[0].mac,
                         command)

    def testfailautomacwithreal(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--automac", "--machine", "ut3c1n4"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Can only automatically generate mac "
                         "addresses for virtual hardware.",
                         command)

    def testverifyaddut3c1n4interface(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.unknown[0].usable[5].mac.lower(),
                         command)
        self.matchclean(out, "Interface: eth1", command)

    def testverifycatut3c1n4interfaces(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"boot", true,\s*\);'
                          % self.net.unknown[0].usable[5].mac,
                          command)

    def testaddinterfaceut3c5(self):
        command = ["add", "interface", "--interface", "oa",
                   "--mac", self.net.unknown[0].usable[6].mac,
                   "--ip", self.net.unknown[0].usable[6].ip,
                   "--chassis", "ut3c5.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifyaddinterfaceut3c5(self):
        command = "show chassis --chassis ut3c5.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Chassis: ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[6].ip,
                         command)
        self.matchoutput(out,
                         "Interface: oa %s boot=False" %
                         self.net.unknown[0].usable[6].mac,
                         command)
        self.matchclean(out, "Interface: oa2", command)

    def testfailaddinterfaceut3c1(self):
        command = ["add", "interface", "--interface", "oa",
                   "--mac", self.net.unknown[0].usable[6].mac,
                   "--ip", self.net.unknown[0].usable[6].ip,
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Mac '%s' already in use: " %
                         self.net.unknown[0].usable[6].mac,
                         command)

    def testverifyfailaddinterfaceut3c1(self):
        command = "show chassis --chassis ut3c1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchclean(out, "Interface: oa", command)

    def testaddinterfacenp997gd1r04(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--mac", self.net.tor_net[3].usable[0].mac,
                   "--ip", self.net.tor_net[3].usable[0].ip,
                   "--tor_switch", "np997gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifyaddinterfacenp997gd1r04(self):
        command = "show tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Tor_switch: np997gd1r04.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.tor_net[3].usable[0].ip,
                         command)
        self.matchoutput(out,
                         "Interface: xge49 %s boot=False" %
                         self.net.tor_net[3].usable[0].mac,
                         command)
        self.matchclean(out, "Interface: xge50", command)

    def testfailaddinterfaceut3dg1r01(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--mac", self.net.tor_net[0].usable[0].mac,
                   "--ip", self.net.tor_net[0].usable[0].ip,
                   "--tor_switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Mac '%s' already in use: " %
                         self.net.tor_net[0].usable[0].mac,
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
                        "--machine", "ut3s01p1a",
                        "--mac", self.net.unknown[0].usable[7].mac])

    def testverifyaddut3s01p1aeth0(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.unknown[0].usable[7].mac.lower(),
                         command)

    def testaddut3s01p1beth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3s01p1b",
                        "--mac", self.net.unknown[0].usable[8].mac])

    def testverifyaddut3s01p1beth0(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.unknown[0].usable[8].mac.lower(),
                         command)

    def testaddut8s02p1eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p1",
                        "--mac", self.net.tor_net[0].usable[1].mac])

    def testverifyaddut8s02p1eth0(self):
        command = "show machine --machine ut8s02p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.tor_net[0].usable[1].mac.lower(),
                         command)

    def testaddut8s02p2eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p2",
                        "--mac", self.net.tor_net[0].usable[2].mac])

    def testverifyaddut8s02p2eth0(self):
        command = "show machine --machine ut8s02p2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.tor_net[0].usable[2].mac.lower(),
                         command)

    def testaddut8s02p3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p3",
                        "--mac", self.net.tor_net[0].usable[3].mac])

    def testverifyaddut8s02p3eth0(self):
        command = "show machine --machine ut8s02p3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.tor_net[0].usable[3].mac.lower(),
                         command)

    def testaddut8s02p4eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p4",
                        "--mac", self.net.tor_net[0].usable[4].mac])

    def testverifyaddut8s04p3eth0(self):
        command = "show machine --machine ut8s02p4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.tor_net[0].usable[4].mac.lower(),
                         command)

    def testaddut8s02p5eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p5",
                        "--mac", self.net.tor_net[0].usable[5].mac])

    def testverifyaddut8s05p3eth0(self):
        command = "show machine --machine ut8s02p5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s boot=True" %
                         self.net.tor_net[0].usable[5].mac.lower(),
                         command)

    def testadd_bootable_no_mac(self):
        """ if name == 'eth0' its bootable. without a mac should fail. """
        command = ["add", "interface", "--interface", "eth0", "--machine",
                   "ut9s03p1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         'Bootable interfaces require a MAC address',
                         command)

    def testadd_no_mac(self):
        """ if it's named eth1 it should work with no mac address """
        self.noouttest(["add", "interface",
                        "--interface", "eth1", "--machine", "ut8s02p3"])

    def testverify_no_mac(self):
        command = "show_machine --machine ut8s02p3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth1 boot=False (no mac addr)",
                         command)

    def testaddhprackinterfaces(self):
        for i in range(51, 100):
            port = i - 50
            machine = "ut9s03p%d" % port
            self.noouttest(["add", "interface", "--interface", "eth0",
                            "--machine", machine,
                            "--mac", self.net.tor_net[1].usable[port].mac])

    def testaddverarirackinterfaces(self):
        for i in range(101, 150):
            port = i - 100
            machine = "ut10s04p%d" % port
            self.noouttest(["add", "interface", "--interface", "eth0",
                            "--machine", machine,
                            "--mac", self.net.tor_net[2].usable[port].mac])
            # Didn't bother putting a tor_switch on this network, although
            # it wouldn't hurt.  At least the first ten (ESX servers) are
            # meant to be left dangling with no IP assigned to test some
            # edge cases.
            self.noouttest(["add", "interface", "--interface", "eth1",
                            "--machine", machine,
                            "--mac", self.net.tor_net[6].usable[port].mac])

    def testadd10gigrackinterfaces(self):
        for port in range(1, 13):
            for (template, offset) in [('ut11s01p%d', 0), ('ut12s02p%d', 12)]:
                machine = template % port
                # Both counts would start at 0 except the tor_net has two
                # tor_switches taking IPs.
                i = port + 1 + offset
                j = port - 1 + offset
                self.noouttest(["add", "interface", "--interface", "eth0",
                                "--machine", machine,
                                "--mac", self.net.tor_net2[2].usable[i].mac])
                self.noouttest(["add", "interface", "--interface", "eth1",
                                "--pg=storage-v701",
                                "--machine", machine, "--mac",
                                self.net.vm_storage_net[0].usable[j].mac])

    def testverifypg(self):
        command = "show machine --machine ut11s01p1"
        out = self.commandtest(command.split())
        self.matchoutput(out, "Port Group: storage-v701", command)

    def testverifycatpg(self):
        command = "cat --machine ut11s01p1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"boot", true,\s*\);'
                          % self.net.tor_net2[2].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"port_group", "storage-v701",\s*\);'
                          % self.net.vm_storage_net[0].usable[0].mac,
                          command)

    # FIXME: Missing a test for an interface with comments.
    # FIXME: Missing a test for adding an interface that already exists.
    # FIXME: Missing a test for a failed DSDB add_host.
    # FIXME: Missing tests around Dell rename hack.

    # Note: additional tests (mostly for --automac) are in the
    # test_add_virtual_hardware module.


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)
