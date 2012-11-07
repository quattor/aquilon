#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand, DummyIP


class TestAddInterface(TestBrokerCommand):

    def testaddut3c5n10eth0_good_mac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--mac", self.net.unknown[0].usable[0].mac.upper()])

    def testaddut3c5n11eth0_mac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n11",
                        "--mac", self.net.netsvcmap.usable[0].mac.upper()])

    def testaddut3c5n12eth0_mac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n12",
                        "--mac", self.net.netperssvcmap.usable[0].mac.upper()])

    def testaddut3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n10",
                        "--mac", self.net.unknown[0].usable[1].mac.lower()])

    def testaddut3c5n10eth1_2(self):
        self.noouttest(["add", "interface", "--interface", "eth1.2",
                        "--machine", "ut3c5n10"])

    def testfailvlanstacking(self):
        command = ["add", "interface", "--interface", "eth1.2.2",
                   "--machine", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Stacking of VLAN interfaces is not allowed.",
                         command)

    def testfailvlanmac(self):
        mac = self.net.unknown[0].usable[-1].mac
        command = ["add", "interface", "--interface", "eth1.3",
                   "--machine", "ut3c5n10", "--mac", mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "VLAN interfaces can not have a distinct MAC address.",
                         command)

    def testfailbadvlan(self):
        command = ["add", "interface", "--interface", "eth1.4096",
                   "--machine", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Illegal VLAN ID 4096: it must be greater than 0 and "
                         "smaller than 4096.",
                         command)

    def testfailbadvlanformat(self):
        command = ["add", "interface", "--interface", "eth1.foo",
                   "--machine", "ut3c5n10", "--type", "vlan"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid VLAN interface name 'eth1.foo'.",
                         command)

    def testfailvlanmodel(self):
        mac = self.net.unknown[0].usable[-1].mac
        command = ["add", "interface", "--interface", "eth1.3",
                   "--machine", "ut3c5n10", "--model", "e1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model/vendor can not be set for a VLAN interface.",
                         command)

    def testaddut3c5n10eth1again(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--machine", "ut3c5n10",
                   "--mac", self.net.unknown[0].usable[-1].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 already has an interface named "
                         "eth1.", command)

    def testaddut3c5n10eth2badmac(self):
        command = ["add", "interface", "--interface", "eth2",
                   "--machine", "ut3c5n10",
                   "--mac", self.net.tor_net[6].usable[0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "MAC address %s is already in use" %
                         self.net.tor_net[6].usable[0].mac, command)

    def testaddut3c5n10eth2_2(self):
        command = ["add", "interface", "--interface", "eth2.2",
                   "--machine", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Parent interface eth2 for VLAN interface "
                         "eth2.2 does not exist", command)

    def testaddut3c5n10eth2automac(self):
        command = ["add", "interface", "--interface", "eth2",
                   "--machine", "ut3c5n10", "--automac"]
        out = self.badrequesttest(command)
        self.matchoutput(out, " Can only automatically generate MAC addresses "
                         "for virtual hardware.", command)

    def testverifyaddut3c5n10interfaces(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]"
                          r"\s+Type: public"
                          r"\s+Vendor: generic Model: generic_nic" %
                          self.net.unknown[0].usable[0].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: eth1 %s$"
                          r"\s+Type: public"
                          r"\s+Vendor: generic Model: generic_nic" %
                          self.net.unknown[0].usable[1].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: eth1\.2 \(no MAC addr\)$"
                          r"\s+Type: vlan"
                          r"\s+Parent Interface: eth1, VLAN ID: 2",
                          command)
        self.matchclean(out, "Port Group", command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\),'
                          % self.net.unknown[0].usable[0].mac,
                          command)
        self.searchoutput(out,
                          r'"eth1", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % self.net.unknown[0].usable[1].mac,
                          command)

    def testaddut3c5n2(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n2",
                        "--mac", self.net.unknown[11].usable[0].mac,
                        "--vendor", "intel", "--model", "e1000"])
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n2",
                        "--mac", self.net.unknown[12].usable[0].mac,
                        "--model", "e1000"])

    def testshowut3c5n2(self):
        command = "show machine --machine ut3c5n2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]"
                          r"\s+Type: public"
                          r"\s+Vendor: intel Model: e1000" %
                          self.net.unknown[11].usable[0].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: eth1 %s$"
                          r"\s+Type: public"
                          r"\s+Vendor: intel Model: e1000" %
                          self.net.unknown[12].usable[0].mac.lower(),
                          command)
        self.matchclean(out, "Port Group", command)

    def testverifyut3c5n2(self):
        command = "cat --machine ut3c5n2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/intel/e1000",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\),\s*'
                          r'"eth1", create\("hardware/nic/intel/e1000",\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % (self.net.unknown[11].usable[0].mac,
                             self.net.unknown[12].usable[0].mac),
                          command)

    def testaddut3c5n3(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n3",
                        "--mac", self.net.unknown[11].usable[1].mac])
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n3",
                        "--mac", self.net.unknown[12].usable[1].mac])

    def testaddut3c5n3bond0(self):
        # Let the broker guess the type
        self.noouttest(["add", "interface", "--interface", "bond0",
                        "--machine", "ut3c5n3"])

    def testenslaveut3c5n3eth0(self):
        self.noouttest(["update", "interface", "--machine", "ut3c5n3",
                        "--interface", "eth0", "--master", "bond0"])

    def testenslaveut3c5n3eth1(self):
        self.noouttest(["update", "interface", "--machine", "ut3c5n3",
                        "--interface", "eth1", "--master", "bond0"])

    def testforbidcircle(self):
        command = ["update", "interface", "--machine", "ut3c5n3",
                   "--interface", "bond0", "--master", "eth0"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Enslaving bonding interface bond0 of machine ut3c5n3 "
                         "would create a circle, which is not allowed.",
                         command)

    def testverifyut3c5n3(self):
        command = "cat --machine ut3c5n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\),\s*'
                          r'"eth1", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % (self.net.unknown[11].usable[1].mac,
                             self.net.unknown[12].usable[1].mac),
                          command)

    def testaddut3c5n4(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n4",
                        "--mac", self.net.unknown[11].usable[2].mac])
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n4",
                        "--mac", self.net.unknown[12].usable[2].mac])

    def testaddut3c5n4br0(self):
        # Specify the interface type explicitely this time
        self.noouttest(["add", "interface", "--interface", "br0",
                        "--type", "bridge", "--machine", "ut3c5n4"])

    def testenslaveut3c5n4eth0(self):
        self.noouttest(["update", "interface", "--machine", "ut3c5n4",
                        "--interface", "eth0", "--master", "br0"])

    def testenslaveut3c5n4eth1(self):
        self.noouttest(["update", "interface", "--machine", "ut3c5n4",
                        "--interface", "eth1", "--master", "br0"])

    def testfailbridgemac(self):
        mac = self.net.unknown[0].usable[-1].mac
        command = ["add", "interface", "--interface", "br1",
                   "--machine", "ut3c5n4", "--mac", mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Bridge interfaces can not have a distinct MAC address.",
                         command)

    def testverifyut3c5n4(self):
        command = "cat --machine ut3c5n4"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\),\s*'
                          r'"eth1", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % (self.net.unknown[11].usable[2].mac,
                             self.net.unknown[12].usable[2].mac),
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
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.unknown[0].usable[2].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: eth1 %s$" %
                          self.net.unknown[0].usable[3].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: bmc %s$" %
                          self.net.unknown[0].usable[4].mac.lower(),
                          command)

    def testaddut3c1n8eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c1n8",
                        "--mac", self.net.unknown[0].usable[18].mac])

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
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\),'
                          % self.net.unknown[0].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"eth1", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
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
                         "MAC address %s is already in use: " %
                         self.net.unknown[0].usable[0].mac,
                         command)

    def testfailaddut3c1n4eth1(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--machine", "ut3c1n4", "--mac", "not-a-mac"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Expected a MAC address", command)

    def testfailautomacwithreal(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--automac", "--machine", "ut3c1n4"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Can only automatically generate MAC "
                         "addresses for virtual hardware.",
                         command)

    def testverifyaddut3c1n4interface(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.unknown[0].usable[5].mac.lower(),
                          command)
        self.matchclean(out, "Interface: eth1", command)

    def testverifycatut3c1n4interfaces(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % self.net.unknown[0].usable[5].mac,
                          command)

    def testaddinterfaceut3c5(self):
        ip = self.net.unknown[0].usable[6]
        self.dsdb_expect_update("ut3c5.aqd-unittest.ms.com", "oa", mac=ip.mac)
        command = ["add", "interface", "--interface", "oa", "--mac", ip.mac,
                   "--chassis", "ut3c5.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddinterfaceut3c5again(self):
        ip = self.net.unknown[0].usable[-1]
        command = ["add", "interface", "--interface", "oa", "--mac", ip.mac,
                   "--chassis", "ut3c5.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "On-board Admin Interface oa of chassis "
                         "ut3c5.aqd-unittest.ms.com already exists.", command)

    def testverifyaddinterfaceut3c5(self):
        command = "show chassis --chassis ut3c5.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Chassis: ut3c5", command)
        self.matchoutput(out,
                         "Primary Name: ut3c5.aqd-unittest.ms.com [%s]" %
                         self.net.unknown[0].usable[6],
                         command)
        self.searchoutput(out,
                          r"Interface: oa %s$" %
                          self.net.unknown[0].usable[6].mac,
                          command)
        self.matchclean(out, "Interface: oa2", command)

    def testfailaddinterfaceut3c1(self):
        command = ["add", "interface", "--interface", "oa2",
                   "--mac", self.net.unknown[0].usable[6].mac,
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use: " %
                         self.net.unknown[0].usable[6].mac,
                         command)

    def testverifyfailaddinterfaceut3c1(self):
        command = "show chassis --chassis ut3c1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Chassis: ut3c1", command)
        self.matchoutput(out, "Primary Name: ut3c1.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "Interface: oa2", command)

    def testfailaddinterfaceut3c1model(self):
        command = ["add", "interface", "--interface", "oa2",
                   "--mac", self.net.unknown[0].usable[-1].mac,
                   "--model", "e1000",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot use argument --model when adding an interface "
                         "to a chassis.",
                         command)

    def testfailaddinterfaceut3c1type(self):
        command = ["add", "interface", "--interface", "oa2",
                   "--mac", self.net.unknown[0].usable[-1].mac,
                   "--type", "vlan",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Only 'oa' is allowed as the interface type "
                         "for chassis.", command)

    def testfailaddinterfaceut3dg1r01(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--mac", self.net.tor_net[0].usable[0].mac,
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use: " %
                         self.net.tor_net[0].usable[0].mac,
                         command)

    def testfailaddinterfaceud3dg1r01model(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--model", "e1000",
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cannot use argument --model when adding an "
                         "interface to a switch.", command)

    def testfailaddinterfaceud3dg1r01type(self):
        command = ["add", "interface", "--interface", "xge49",
                   "--type", "vlan",
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Interface type vlan is not allowed for "
                         "switches.", command)

    def testverifyfailaddinterfaceut3dg1r01(self):
        command = "show tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out, "Primary Name: ut3gd1r01.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "Interface: xge49", command)

    def testaddvirtualswitchinterface(self):
        command = ["add", "interface", "--interface", "vlan110",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testaddloopback(self):
        command = ["add", "interface", "--interface", "loop0",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testfailloopbackmac(self):
        command = ["add", "interface", "--interface", "loop1",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--mac", self.net.unknown[17][0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Loopback interfaces cannot have a MAC address.",
                         command)

    def testverifyut3gd1r04(self):
        command = ["show", "switch", "--switch",
                   "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Interface: xge49 %s" % self.net.tor_net[6].usable[0].mac,
                         command)
        self.matchoutput(out, "Interface: vlan110 (no MAC addr)", command)
        self.matchoutput(out, "Interface: loop0 (no MAC addr)", command)
        self.matchclean(out, "loop1", command)

    # These two will eventually be created when testing the addition
    # of a whole rack of machines based on a CheckNet sweep.
    def testaddut3s01p1aeth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3s01p1a",
                        "--mac", self.net.unknown[0].usable[7].mac])

    def testverifyaddut3s01p1aeth0(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.unknown[0].usable[7].mac.lower(),
                          command)

    def testaddut3s01p1beth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3s01p1b",
                        "--mac", self.net.unknown[0].usable[8].mac])

    def testverifyaddut3s01p1beth0(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.unknown[0].usable[8].mac.lower(),
                          command)

    def testaddut8s02p1eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p1",
                        "--mac", self.net.tor_net[0].usable[1].mac])

    def testverifyaddut8s02p1eth0(self):
        command = "show machine --machine ut8s02p1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.tor_net[0].usable[1].mac.lower(),
                          command)

    def testaddut8s02p2eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p2",
                        "--mac", self.net.tor_net[0].usable[2].mac])

    def testverifyaddut8s02p2eth0(self):
        command = "show machine --machine ut8s02p2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.tor_net[0].usable[2].mac.lower(),
                          command)

    def testaddut8s02p3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p3",
                        "--mac", self.net.tor_net[0].usable[3].mac])

    def testverifyaddut8s02p3eth0(self):
        command = "show machine --machine ut8s02p3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.tor_net[0].usable[3].mac.lower(),
                          command)

    def testaddut8s02p4eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p4",
                        "--mac", self.net.tor_net[0].usable[4].mac])

    def testverifyaddut8s04p3eth0(self):
        command = "show machine --machine ut8s02p4"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                         self.net.tor_net[0].usable[4].mac.lower(),
                         command)

    def testaddut8s02p5eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut8s02p5",
                        "--mac", self.net.tor_net[0].usable[5].mac])

    def testverifyaddut8s05p3eth0(self):
        command = "show machine --machine ut8s02p5"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net.tor_net[0].usable[5].mac.lower(),
                          command)

    def testadd_bootable_no_mac(self):
        """ if name == 'eth0' its bootable. without a MAC should fail. """
        command = ["add", "interface", "--interface", "eth0", "--machine",
                   "ut9s03p1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         'Bootable interfaces require a MAC address',
                         command)

    def testadd_no_mac(self):
        """ if it's named eth1 it should work with no MAC address """
        self.noouttest(["add", "interface",
                        "--interface", "eth1", "--machine", "ut8s02p3"])

    def testverify_no_mac(self):
        command = "show_machine --machine ut8s02p3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth1 \(no MAC addr\)$",
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
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\),'
                          % self.net.tor_net2[2].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"eth1", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"port_group", "storage-v701"\s*\)\s*\);'
                          % self.net.vm_storage_net[0].usable[0].mac,
                          command)

    def testaddharackinterfaces(self):
        for port in range(1, 25):
            for (template, netoff) in [('ut13s03p%d', 3), ('np13s03p%d', 4)]:
                machine = template % port
                self.noouttest(["add", "interface", "--interface", "eth0",
                                "--machine", machine,
                                "--mac", self.net.tor_net2[netoff].usable[port].mac])

    def testaddut3c5n5(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n5",
                        "--mac", self.net.vpls[0].usable[1].mac])

    def testaddnp3c5n5(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "np3c5n5",
                        "--mac", self.net.vpls[0].usable[2].mac])

    def testaddut3c5n6(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n6",
                        "--mac", self.net.unknown[0].usable[19].mac])

    def testaddut3c5n7(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n7",
                        "--mac", self.net.unknown[0].usable[20].mac])
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n7",
                        "--mac", self.net.unknown[0].usable[21].mac])
        self.noouttest(["add", "interface", "--interface", "eth2",
                        "--machine", "ut3c5n7",
                        "--mac", self.net.unknown[0].usable[22].mac])

    def testaddut3c5n8(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n8",
                        "--mac", self.net.unknown[0].usable[23].mac])
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n8",
                        "--mac", self.net.unknown[14].usable[0].mac])

    # FIXME: Missing a test for a failed DSDB add_host.
    # FIXME: Missing tests around Dell rename hack.

    # Note: additional tests (mostly for --automac) are in the
    # test_add_virtual_hardware module.

    def testaddjackmac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "jack",
                        "--comments", "interface for jack",
                        "--mac", self.net.unknown[0].usable[17].mac.upper()])

    def testverifyjackmac(self):
        command = "show machine --machine jack"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s" %
                         self.net.unknown[0].usable[17].mac.lower(),
                         command)
        self.searchoutput(out, r"\s+Comments: interface for jack",
                          command)

    def testaddfilermac(self):
        self.noouttest(["add", "interface", "--machine", "filer1",
                        "--interface", "e4a"])
        self.noouttest(["add", "interface", "--machine", "filer1",
                        "--interface", "e4b"])
        self.noouttest(["add", "interface", "--machine", "filer1",
                        "--interface", "v0", "--type", "bonding"])
        self.noouttest(["update", "interface", "--machine", "filer1",
                        "--master", "v0", "--interface", "e4a"])
        self.noouttest(["update", "interface", "--machine", "filer1",
                        "--master", "v0", "--interface", "e4b"])
        self.noouttest(["update", "interface", "--machine", "filer1",
                        "--interface", "v0", "--boot"])

    def testfailunknowntype(self):
        command = ["add", "interface", "--machine", "ut3c1n3",
                   "--interface", "eth2", "--type", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid interface type 'no-such-type'.", command)

    def testfailbadtype(self):
        command = ["add", "interface", "--machine", "ut3c1n3",
                   "--interface", "eth2", "--type", "oa"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Interface type 'oa' is not valid for machines.",
                         command)

    def testaddf5iface(self):
        ip = DummyIP(self.net.unknown[16].ip)
        command = ["add", "interface", "--machine", "f5test",
                   "--interface", "eth0", "--mac", ip.mac]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)
