#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the add interface command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddInterface(TestBrokerCommand):
    def testaddut3c5n10eth0_bootable_no_mac(self):
        """ if name == 'eth0' its bootable. without a MAC should fail. """
        command = ["add", "interface", "--interface", "eth0", "--machine",
                   "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         'Bootable interfaces require a MAC address',
                         command)

    def testaddut3c5n10eth0_good_mac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--mac", self.net["unknown0"].usable[0].mac.upper()])

    def testaddut3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c5n10",
                        "--mac", self.net["unknown0"].usable[1].mac.lower()])

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
        mac = self.net["unknown0"].usable[-1].mac
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
                   "--machine", "ut3c5n10", "--iftype", "vlan"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid VLAN interface name 'eth1.foo'.",
                         command)

    def testfailvlanmodel(self):
        mac = self.net["unknown0"].usable[-1].mac
        command = ["add", "interface", "--interface", "eth1.3",
                   "--machine", "ut3c5n10", "--model", "e1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model/vendor can not be set for a VLAN interface.",
                         command)

    def testaddut3c5n10eth1again(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--machine", "ut3c5n10",
                   "--mac", self.net["unknown0"].usable[-1].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Bad Request: Public Interface eth1 of machine "
                         "ut3c5n10 already exists.", command)

    def testaddut3c5n10eth2badmac(self):
        command = ["add", "interface", "--interface", "eth2",
                   "--machine", "ut3c5n10",
                   "--mac", self.net["verari_eth1"].usable[0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "MAC address %s is already in use" %
                         self.net["verari_eth1"].usable[0].mac, command)

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
                          self.net["unknown0"].usable[0].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: eth1 %s$"
                          r"\s+Type: public"
                          r"\s+Vendor: generic Model: generic_nic" %
                          self.net["unknown0"].usable[1].mac.lower(),
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
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["unknown0"].usable[0].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["unknown0"].usable[1].mac,
                          command)

    def testverifyut3c5n2(self):
        command = "cat --machine ut3c5n2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/intel/e1000",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);\s*'
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/intel/e1000",\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % (self.net["zebra_eth0"].usable[0].mac,
                             self.net["zebra_eth1"].usable[0].mac),
                          command)

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
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);\s*'
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % (self.net["zebra_eth0"].usable[1].mac,
                             self.net["zebra_eth1"].usable[1].mac),
                          command)

    def testaddut3c5n4br0(self):
        # Specify the interface type explicitely this time
        self.noouttest(["add", "interface", "--interface", "br0",
                        "--iftype", "bridge", "--machine", "ut3c5n4"])

    def testenslaveut3c5n4eth0(self):
        self.noouttest(["update", "interface", "--machine", "ut3c5n4",
                        "--interface", "eth0", "--master", "br0"])

    def testenslaveut3c5n4eth1(self):
        self.noouttest(["update", "interface", "--machine", "ut3c5n4",
                        "--interface", "eth1", "--master", "br0"])

    def testfailbridgemac(self):
        mac = self.net["unknown0"].usable[-1].mac
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
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);\s*'
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % (self.net["zebra_eth0"].usable[2].mac,
                             self.net["zebra_eth1"].usable[2].mac),
                          command)

    def testaddut3c1n3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c1n3",
                        "--mac", self.net["unknown0"].usable[2].mac.upper()])

    def testaddut3c1n3eth1(self):
        testmac = []
        for i in self.net["unknown0"].usable[3].mac.split(":"):
            if i.startswith("0"):
                testmac.append(i[1])
            else:
                testmac.append(i)
        self.noouttest(["add", "interface", "--interface", "eth1",
                        "--machine", "ut3c1n3", "--mac", ":".join(testmac)])

    def testaddut3c1n3bmc(self):
        self.noouttest(["add", "interface", "--interface", "bmc",
                        "--machine", "ut3c1n3",
                        "--mac", self.net["unknown0"].usable[4].mac.lower()])

    def testverifyaddut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net["unknown0"].usable[2].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: eth1 %s$" %
                          self.net["unknown0"].usable[3].mac.lower(),
                          command)
        self.searchoutput(out,
                          r"Interface: bmc %s$" %
                          self.net["unknown0"].usable[4].mac.lower(),
                          command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["unknown0"].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["unknown0"].usable[3].mac,
                          command)
        self.searchoutput(out,
                          r'"console/bmc" = nlist\(\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % (self.net["unknown0"].usable[4].mac.lower()),
                          command)

    def testaddut3c1n4eth0(self):
        testmac = "".join(self.net["unknown0"].usable[5].mac.split(":"))
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3c1n4", "--mac", testmac])

    def testfailaddut3c1n4eth1(self):
        command = ["add", "interface", "--interface", "eth1",
                   "--machine", "ut3c1n4",
                   "--mac", self.net["unknown0"].usable[0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use: " %
                         self.net["unknown0"].usable[0].mac,
                         command)

    def testfailaddut3c1n4eth1badmac(self):
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
                          self.net["unknown0"].usable[5].mac.lower(),
                          command)
        self.matchclean(out, "Interface: eth1", command)

    def testverifycatut3c1n4interfaces(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["unknown0"].usable[5].mac,
                          command)

    def testaddinterfaceut3c5(self):
        ip = self.net["unknown0"].usable[6]
        self.dsdb_expect_update("ut3c5.aqd-unittest.ms.com", "oa", mac=ip.mac)
        command = ["update", "interface", "--interface", "oa", "--mac", ip.mac,
                   "--chassis", "ut3c5.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddinterfaceut3c5again(self):
        ip = self.net["unknown0"].usable[-1]
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
                         self.net["unknown0"].usable[6],
                         command)
        self.searchoutput(out,
                          r"Interface: oa %s$" %
                          self.net["unknown0"].usable[6].mac,
                          command)
        self.matchclean(out, "Interface: oa2", command)

    def testfailaddinterfaceut3c1(self):
        command = ["add", "interface", "--interface", "oa2",
                   "--mac", self.net["unknown0"].usable[6].mac,
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use: " %
                         self.net["unknown0"].usable[6].mac,
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
                   "--mac", self.net["unknown0"].usable[-1].mac,
                   "--model", "e1000",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot use argument --model when adding an interface "
                         "to a chassis.",
                         command)

    def testfailaddinterfaceut3c1type(self):
        command = ["add", "interface", "--interface", "oa2",
                   "--mac", self.net["unknown0"].usable[-1].mac,
                   "--iftype", "vlan",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Only 'oa' is allowed as the interface type "
                         "for chassis.", command)

    def testfailaddinterfaceut3dg1r01(self):
        command = ["add", "interface", "--interface", "xge1",
                   "--iftype", "physical",
                   "--mac", self.net["tor_net_0"].usable[0].mac,
                   "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use: " %
                         self.net["tor_net_0"].usable[0].mac,
                         command)

    def testfailaddinterfaceud3dg1r01model(self):
        command = ["add", "interface", "--interface", "xge1",
                   "--iftype", "physical", "--model", "e1000",
                   "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cannot use argument --model when adding an "
                         "interface to a network device.", command)

    def testfailaddinterfaceud3dg1r01type(self):
        command = ["add", "interface", "--interface", "xge1",
                   "--iftype", "vlan",
                   "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Interface type vlan is not allowed for "
                         "network devices.", command)

    def testverifyfailaddinterfaceut3dg1r01(self):
        command = "show network_device --network_device ut3gd1r01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out, "Primary Name: ut3gd1r01.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "Interface: xge1", command)

    def testaddvirtualswitchinterface(self):
        command = ["add", "interface", "--interface", "vlan110",
                   "--iftype", "virtual",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testaddloopback(self):
        command = ["add", "interface", "--interface", "loop0",
                   "--iftype", "loopback",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testfailloopbackmac(self):
        command = ["add", "interface", "--interface", "loop1",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                   "--iftype", "loopback",
                   "--mac", self.net["autopg1"][0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Loopback interfaces cannot have a MAC address.",
                         command)

    def testverifyut3gd1r04(self):
        command = ["show", "network_device", "--network_device",
                   "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Interface: xge49 %s" % self.net["verari_eth1"].usable[0].mac,
                         command)
        self.matchoutput(out, "Interface: vlan110 (no MAC addr)", command)
        self.matchoutput(out, "Interface: loop0 (no MAC addr)", command)
        self.matchclean(out, "loop1", command)

    # These two will eventually be created when testing the addition
    # of a whole rack of machines based on switch discovery.
    def testaddut3s01p1aeth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3s01p1a",
                        "--mac", self.net["unknown0"].usable[7].mac])

    def testverifyaddut3s01p1aeth0(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net["unknown0"].usable[7].mac.lower(),
                          command)

    def testaddut3s01p1beth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "ut3s01p1b",
                        "--mac", self.net["unknown0"].usable[8].mac])

    def testverifyaddut3s01p1beth0(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r"Interface: eth0 %s \[boot, default_route\]" %
                          self.net["unknown0"].usable[8].mac.lower(),
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

    def testverifycatpg(self):
        command = "cat --machine ut11s01p1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["vmotion_net"].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"port_group", "storage-v701"\s*\);'
                          % self.net["vm_storage_net"].usable[0].mac,
                          command)

    # FIXME: Missing a test for a failed DSDB add_host.
    # FIXME: Missing tests around Dell rename hack.

    # Note: additional tests (mostly for --automac) are in the
    # test_add_virtual_hardware module.

    def testaddjackmac(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", "jack",
                        "--comments", "interface for jack",
                        "--mac", self.net["unknown0"].usable[17].mac.upper()])

    def testverifyjackmac(self):
        command = "show machine --machine jack"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Interface: eth0 %s" %
                         self.net["unknown0"].usable[17].mac.lower(),
                         command)
        self.searchoutput(out, r"\s+Comments: interface for jack",
                          command)

    def testaddfilermac(self):
        self.noouttest(["add", "interface", "--machine", "filer1",
                        "--interface", "e4a"])
        self.noouttest(["add", "interface", "--machine", "filer1",
                        "--interface", "e4b"])
        self.noouttest(["add", "interface", "--machine", "filer1",
                        "--interface", "v0", "--iftype", "bonding"])
        self.noouttest(["update", "interface", "--machine", "filer1",
                        "--master", "v0", "--interface", "e4a"])
        self.noouttest(["update", "interface", "--machine", "filer1",
                        "--master", "v0", "--interface", "e4b"])
        self.noouttest(["update", "interface", "--machine", "filer1",
                        "--interface", "v0", "--boot"])

    def testfailunknowntype(self):
        command = ["add", "interface", "--machine", "ut3c1n3",
                   "--interface", "eth2", "--iftype", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid interface type 'no-such-type'.", command)

    def testfailbadtype(self):
        command = ["add", "interface", "--machine", "ut3c1n3",
                   "--interface", "eth2", "--iftype", "oa"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Interface type 'oa' is not valid for machines.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)
