#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the add network device command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from netdevtest import VerifyNetworkDeviceMixin


class TestAddNetworkDevice(TestBrokerCommand, VerifyNetworkDeviceMixin):

    # Testing that add network device does not allow a blade....
    def testrejectut3gd1r03(self):
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut3gd1r03.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "hs21-8853l5u",
                   "--ip", self.net["tor_net_9"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "This command can only be used "
                         "to add network devices.", command)

    def testverifyrejectut3gd1r03(self):
        command = "show network_device --network_device ut3gd1r03.aqd-unittest.ms.com"
        out = self.notfoundtest(command.split(" "))

    def testaddut3gd1r01(self):
        ip = self.net["tor_net_12"].usable[0]
        self.dsdb_expect_add("ut3gd1r01.aqd-unittest.ms.com", ip, "xge")
        self.successtest(["add", "network_device", "--type", "bor",
                          "--network_device", "ut3gd1r01.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3",
                          "--model", "uttorswitch", "--serial", "SNgd1r01"])
        self.dsdb_verify()

    def testaddut3gd1r04(self):
        ip = self.net["verari_eth1"].usable[0]
        self.dsdb_expect_add("ut3gd1r04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac, comments="Some switch comments")
        self.successtest(["add", "network_device", "--type", "tor",
                          "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                          "--ip", ip, "--mac", ip.mac, "--interface", "xge49",
                          "--rack", "ut3", "--model", "temp_switch",
                          "--comments", "Some switch comments"])
        self.dsdb_verify()

    def testaddut3gd1r05(self):
        ip = self.net["tor_net_7"].usable[0]
        self.dsdb_expect_add("ut3gd1r05.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "network_device", "--type", "tor",
                          "--network_device", "ut3gd1r05.aqd-unittest.ms.com",
                          "--ip", ip, "--interface", "xge49",
                          "--rack", "ut3", "--model", "temp_switch",
                          "--vendor", "generic"])
        self.dsdb_verify()

    def testaddut3gd1r06(self):
        ip = self.net["tor_net_8"].usable[0]
        self.dsdb_expect_add("ut3gd1r06.aqd-unittest.ms.com", ip, "xge")
        self.successtest(["add", "network_device", "--type", "tor",
                          "--network_device", "ut3gd1r06.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3", "--model", "temp_switch",
                          "--vendor", "generic"])
        self.dsdb_verify()

    def testaddut3gd1r07(self):
        ip = self.net["tor_net_9"].usable[0]
        self.dsdb_expect_add("ut3gd1r07.aqd-unittest.ms.com", ip, "xge")
        self.successtest(["add", "network_device", "--type", "bor",
                          "--network_device", "ut3gd1r07.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3", "--model", "temp_switch"])
        self.dsdb_verify()

    def testaddnp06bals03(self):
        self.dsdb_expect_add("np06bals03.ms.com", "172.31.64.69",
                             "gigabitethernet0_1", "00:18:b1:89:86:00")
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "np06bals03.ms.com",
                   "--rack", "np7", "--model", "rs g8000",
                   "--interface", "gigabitethernet0/1",
                   "--mac", "0018b1898600", "--ip", "172.31.64.69"]
        err = self.statustest(command)
        self.dsdb_verify()
        self.matchoutput(err,
                         "Moving rack np7 into bunker nyb10.np based on "
                         "network tagging.",
                         command)

    def testaddnp06fals01(self):
        self.dsdb_expect_add("np06fals01.ms.com", "172.31.88.5", "xge49",
                             "00:1c:f6:99:e5:c1")
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "np06fals01.ms.com",
                   "--rack", "np7", "--model", "ws-c2960-48tt-l",
                   "--interface", "xge49",
                   "--mac", "001cf699e5c1", "--ip", "172.31.88.5"]
        err = self.statustest(command)
        self.dsdb_verify()
        self.matchoutput(err,
                         "Bunker violation: rack np7 is inside bunker "
                         "nyb10.np, but network nyp_hpl_2960_verari_mnmt is "
                         "not bunkerized.",
                         command)

    def testaddut01ga1s02(self):
        ip = self.net["tor_net_0"].usable[0]
        self.dsdb_expect_add("ut01ga1s02.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga1s02.aqd-unittest.ms.com",
                   "--rack", "ut8", "--model", "rs g8000",
                   "--interface", "xge49", "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga1s03(self):
        ip = self.net["hp_eth0"].usable[0]
        self.dsdb_expect_add("ut01ga1s03.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga1s03.aqd-unittest.ms.com",
                   "--rack", "ut9", "--model", "rs g8000",
                   "--interface", "xge49", "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga1s04(self):
        ip = self.net["verari_eth0"].usable[0]
        self.dsdb_expect_add("ut01ga1s04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga1s04.aqd-unittest.ms.com",
                   "--rack", "ut10", "--model", "rs g8000",
                   "--interface", "xge49", "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga2s01(self):
        ip = self.net["vmotion_net"].usable[0]
        self.dsdb_expect_add("ut01ga2s01.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s01.aqd-unittest.ms.com",
                   "--rack", "ut11", "--model", "rs g8000",
                   "--interface", "xge49", "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga2s02(self):
        ip = self.net["vmotion_net"].usable[1]
        self.dsdb_expect_add("ut01ga2s02.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s02.aqd-unittest.ms.com",
                   "--rack", "ut12", "--model", "rs g8000",
                   "--interface", "xge49", "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga2s03(self):
        ip = self.net["esx_bcp_ut"].usable[0]
        self.dsdb_expect_add("ut01ga2s03.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s03.aqd-unittest.ms.com",
                   "--rack", "ut13",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddnp01ga2s03(self):
        ip = self.net["esx_bcp_np"].usable[0]
        self.dsdb_expect_add("np01ga2s03.one-nyp.ms.com", ip, "xge49", ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "np01ga2s03.one-nyp.ms.com",
                   "--rack", "np13",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testrejectut3gd1r99(self):
        command = ["add", "network_device", "--network_device", "ut3gd1r99.aqd-unittest.ms.com",
                   "--type", "bor", "--ip", self.net["tor_net_9"].usable[0],
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use" %
                         self.net["tor_net_9"].usable[0],
                         command)

    def testverifyaddut3gd1r01(self):
        ip = self.net["tor_net_12"].usable[0]
        self.verifynetdev("ut3gd1r01.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", "SNgd1r01", switch_type='bor', ip=ip)

        command = ["show", "network_device", "--network_device",
                   "ut3gd1r01.aqd-unittest.ms.com", "--format", "csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,SNgd1r01,," % ip, command)

    def testverifyaddut3gd1r04(self):
        self.verifynetdev("ut3gd1r04.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net["verari_eth1"].usable[0],
                          mac=self.net["verari_eth1"].usable[0].mac,
                          interface="xge49",
                          comments="Some switch comments")

    def testverifyaddut3gd1r05(self):
        self.verifynetdev("ut3gd1r05.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net["tor_net_7"].usable[0],
                          interface="xge49")

    def testverifyaddut3gd1r06(self):
        self.verifynetdev("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net["tor_net_8"].usable[0])

    def testverifyaddut3gd1r07(self):
        self.verifynetdev("ut3gd1r07.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='bor',
                          ip=self.net["tor_net_9"].usable[0])

    def testverifynp06bals03(self):
        self.verifynetdev("np06bals03.ms.com",
                          "bnt", "rs g8000", "np7", "g", "1",
                          ip="172.31.64.69", mac="00:18:b1:89:86:00",
                          interface="gigabitethernet0/1")

    def testverifynp06fals01(self):
        self.verifynetdev("np06fals01.ms.com",
                          "cisco", "ws-c2960-48tt-l", "np7", "g", "1",
                          ip="172.31.88.5", mac="00:1c:f6:99:e5:c1",
                          interface="xge49")

    def testverifyut01ga1s02(self):
        self.verifynetdev("ut01ga1s02.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut8", "g", "2",
                          ip=str(self.net["tor_net_0"].usable[0]),
                          mac=self.net["tor_net_0"].usable[0].mac,
                          interface="xge49")

    def testverifyut01ga1s03(self):
        self.verifynetdev("ut01ga1s03.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut9", "g", "3",
                          ip=str(self.net["hp_eth0"].usable[0]),
                          mac=self.net["hp_eth0"].usable[0].mac,
                          interface="xge49")

    def testverifyut01ga1s04(self):
        self.verifynetdev("ut01ga1s04.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut10", "g", "4",
                          ip=str(self.net["verari_eth0"].usable[0]),
                          mac=self.net["verari_eth0"].usable[0].mac,
                          interface="xge49")

    def testrejectbadlabelimplicit(self):
        command = ["add", "network_device", "--network_device", "not-alnum.aqd-unittest.ms.com",
                   "--type", "bor", "--ip", self.net["tor_net_9"].usable[-1],
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not deduce a valid hardware label",
                         command)

    def testrejectbadlabelexplicit(self):
        command = ["add", "network_device", "--network_device", "ut3gd1r99.aqd-unittest.ms.com",
                   "--label", "not-alnum",
                   "--type", "bor", "--ip", self.net["tor_net_9"].usable[-1],
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal hardware label format 'not-alnum'.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
