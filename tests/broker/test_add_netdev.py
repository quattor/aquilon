#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
    def test_100_add_ut3gd1r01(self):
        ip = self.net["tor_net_12"].usable[0]
        self.dsdb_expect_add("ut3gd1r01.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "network_device", "--type", "bor",
                          "--network_device", "ut3gd1r01.aqd-unittest.ms.com",
                          "--ip", ip, "--interface", "xge49",
                          "--iftype", "physical", "--rack", "ut3",
                          "--model", "uttorswitch", "--serial", "SNgd1r01"])
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut3gd1r01')
        self.check_plenary_exists('hostdata', 'ut3gd1r01.aqd-unittest.ms.com')

        self.verifynetdev("ut3gd1r01.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", "SNgd1r01", switch_type='bor', ip=ip,
                          interface="xge49")

    def test_101_verify_ut3gd1r01_csv(self):
        ip = self.net["tor_net_12"].usable[0]
        command = ["show", "network_device", "--network_device",
                   "ut3gd1r01.aqd-unittest.ms.com", "--format", "csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,SNgd1r01,," % ip, command)

    def test_105_add_ut3gd1r04(self):
        ip = self.net["verari_eth1"].usable[0]
        self.dsdb_expect_add("ut3gd1r04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac, comments="Some switch comments")
        self.successtest(["add", "network_device", "--type", "tor",
                          "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                          "--ip", ip, "--mac", ip.mac, "--interface", "xge49",
                          "--iftype", "physical",
                          "--rack", "ut3", "--model", "temp_switch",
                          "--comments", "Some switch comments"])
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut3gd1r04')
        self.check_plenary_exists('hostdata', 'ut3gd1r04.aqd-unittest.ms.com')

        self.verifynetdev("ut3gd1r04.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=ip, mac=ip.mac, interface="xge49",
                          comments="Some switch comments")

    def test_110_add_ut3gd1r05(self):
        ip = self.net["ut_net_mgmt"].usable[0]
        self.dsdb_expect_add("ut3gd1r05.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "network_device", "--type", "tor",
                          "--network_device", "ut3gd1r05.aqd-unittest.ms.com",
                          "--ip", ip, "--interface", "xge49",
                          "--iftype", "physical",
                          "--rack", "ut3", "--model", "temp_switch",
                          "--vendor", "generic"])
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut3gd1r05')
        self.check_plenary_exists('hostdata', 'ut3gd1r05.aqd-unittest.ms.com')

        self.verifynetdev("ut3gd1r05.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=ip, interface="xge49")

    def test_115_add_ut3gd1r06(self):
        ip = self.net["ut_net_mgmt"].usable[1]
        self.dsdb_expect_add("ut3gd1r06.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "network_device", "--type", "tor",
                          "--network_device", "ut3gd1r06.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3", "--model", "temp_switch",
                          "--vendor", "generic", "--interface", "xge49",
                          "--iftype", "physical"])
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut3gd1r06')
        self.check_plenary_exists('hostdata', 'ut3gd1r06.aqd-unittest.ms.com')

        self.verifynetdev("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=ip, interface="xge49")

    def test_120_add_ut3gd1r07(self):
        ip = self.net["ut_net_mgmt"].usable[2]
        self.dsdb_expect_add("ut3gd1r07.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "network_device", "--type", "bor",
                          "--network_device", "ut3gd1r07.aqd-unittest.ms.com",
                          "--ip", ip, "--interface", "xge49",
                          "--iftype", "physical", "--rack", "ut3",
                          "--model", "temp_switch"])
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut3gd1r07')
        self.check_plenary_exists('hostdata', 'ut3gd1r07.aqd-unittest.ms.com')

        self.verifynetdev("ut3gd1r07.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='bor',
                          ip=ip, interface="xge49")

    def test_125_add_switch_in_building(self):
        # Located in a building, not in a rack
        ip = self.net["ut_net_mgmt"].usable[3]
        self.dsdb_expect_add("switchinbuilding.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "network_device", "--type", "bor",
                          "--network_device", "switchinbuilding.aqd-unittest.ms.com",
                          "--ip", ip, "--interface", "xge49",
                          "--iftype", "physical",
                          "--building", "ut", "--model", "temp_switch"])
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut',
                                  'switchinbuilding')
        self.check_plenary_exists('hostdata', 'switchinbuilding.aqd-unittest.ms.com')

    def test_130_add_np06bals03(self):
        self.dsdb_expect_add("np06bals03.ms.com", "172.31.64.69",
                             "gigabitethernet0_1", "00:18:b1:89:86:00")
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "np06bals03.ms.com",
                   "--rack", "np7", "--model", "rs g8000",
                   "--interface", "gigabitethernet0/1",
                   "--iftype", "physical",
                   "--mac", "0018b1898600", "--ip", "172.31.64.69"]
        err = self.statustest(command)
        self.dsdb_verify()
        self.matchoutput(err,
                         "Moving rack np7 into bunker nyb10.np based on "
                         "network tagging.",
                         command)
        self.check_plenary_exists('network_device', 'americas', 'np', 'np06bals03')
        self.check_plenary_exists('hostdata', 'np06bals03.ms.com')

        self.verifynetdev("np06bals03.ms.com",
                          "bnt", "rs g8000", "np7", "g", "1",
                          ip="172.31.64.69", mac="00:18:b1:89:86:00",
                          interface="gigabitethernet0/1")

    def test_135_add_np06fals01(self):
        self.dsdb_expect_add("np06fals01.ms.com", "172.31.88.5", "xge49",
                             "00:1c:f6:99:e5:c1")
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "np06fals01.ms.com",
                   "--rack", "np7", "--model", "ws-c2960-48tt-l",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", "001cf699e5c1", "--ip", "172.31.88.5"]
        err = self.statustest(command)
        self.dsdb_verify()
        self.matchoutput(err,
                         "Bunker violation: rack np7 is inside bunker "
                         "nyb10.np, but network nyp_hpl_2960_verari_mnmt is "
                         "not bunkerized.",
                         command)
        self.check_plenary_exists('network_device', 'americas', 'np', 'np06fals01')
        self.check_plenary_exists('hostdata', 'np06fals01.ms.com')

        self.verifynetdev("np06fals01.ms.com",
                          "cisco", "ws-c2960-48tt-l", "np7", "g", "1",
                          ip="172.31.88.5", mac="00:1c:f6:99:e5:c1",
                          interface="xge49")

    def test_140_add_ut01ga1s02(self):
        ip = self.net["tor_net_0"].usable[0]
        self.dsdb_expect_add("ut01ga1s02.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga1s02.aqd-unittest.ms.com",
                   "--rack", "ut8", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut01ga1s02')
        self.check_plenary_exists('hostdata', 'ut01ga1s02.aqd-unittest.ms.com')

        self.verifynetdev("ut01ga1s02.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut8", "g", "2",
                          ip=ip, mac=ip.mac, interface="xge49")

    def test_145_add_ut01ga1s03(self):
        ip = self.net["hp_eth0"].usable[0]
        self.dsdb_expect_add("ut01ga1s03.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga1s03.aqd-unittest.ms.com",
                   "--rack", "ut9", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut01ga1s03')
        self.check_plenary_exists('hostdata', 'ut01ga1s03.aqd-unittest.ms.com')

        self.verifynetdev("ut01ga1s03.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut9", "g", "3",
                          ip=ip, mac=ip.mac, interface="xge49")

    def test_150_add_ut01ga1s04(self):
        ip = self.net["verari_eth0"].usable[0]
        self.dsdb_expect_add("ut01ga1s04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga1s04.aqd-unittest.ms.com",
                   "--rack", "ut10", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut01ga1s04')
        self.check_plenary_exists('hostdata', 'ut01ga1s04.aqd-unittest.ms.com')

        self.verifynetdev("ut01ga1s04.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut10", "g", "4",
                          ip=ip, mac=ip.mac, interface="xge49")

    def test_160_add_ut01ga2s01(self):
        ip = self.net["vmotion_net"].usable[0]
        self.dsdb_expect_add("ut01ga2s01.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s01.aqd-unittest.ms.com",
                   "--rack", "ut11", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut01ga2s01')
        self.check_plenary_exists('hostdata', 'ut01ga2s01.aqd-unittest.ms.com')

    def test_161_add_ut01ga2s02(self):
        ip = self.net["vmotion_net"].usable[1]
        self.dsdb_expect_add("ut01ga2s02.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s02.aqd-unittest.ms.com",
                   "--rack", "ut12", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut01ga2s02')
        self.check_plenary_exists('hostdata', 'ut01ga2s02.aqd-unittest.ms.com')

    def test_162_add_ut01ga2s03(self):
        ip = self.net["ut_net_mgmt"].usable[5]
        self.dsdb_expect_add("ut01ga2s03.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s03.aqd-unittest.ms.com",
                   "--rack", "ut12", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()

    def test_162_add_ut01ga2s04(self):
        ip = self.net["ut_net_mgmt"].usable[6]
        self.dsdb_expect_add("ut01ga2s04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s04.aqd-unittest.ms.com",
                   "--rack", "ut12", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()

    def test_170_add_ut01ga2s05(self):
        ip = self.net["esx_bcp_ut"].usable[0]
        self.dsdb_expect_add("ut01ga2s05.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "ut01ga2s05.aqd-unittest.ms.com",
                   "--rack", "ut13",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut01ga2s05')
        self.check_plenary_exists('hostdata', 'ut01ga2s05.aqd-unittest.ms.com')

    def test_171_add_np01ga2s05(self):
        ip = self.net["esx_bcp_np"].usable[0]
        self.dsdb_expect_add("np01ga2s05.one-nyp.ms.com", ip, "xge49", ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "np01ga2s05.one-nyp.ms.com",
                   "--rack", "np13",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--iftype", "physical", "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()
        self.check_plenary_exists('network_device', 'americas', 'np', 'np01ga2s05')
        self.check_plenary_exists('hostdata', 'np01ga2s05.one-nyp.ms.com')

    def test_175_add_utpgsw0(self):
        ip = self.net["ut_net_mgmt"].usable[7]
        self.dsdb_expect_add("utpgsw0.aqd-unittest.ms.com", ip, "xge49", ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "utpgsw0.aqd-unittest.ms.com",
                   "--rack", "ut12", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()

    def test_175_add_utpgsw1(self):
        ip = self.net["ut_net_mgmt"].usable[8]
        self.dsdb_expect_add("utpgsw1.aqd-unittest.ms.com", ip, "xge49", ip.mac)
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "utpgsw1.aqd-unittest.ms.com",
                   "--rack", "ut12", "--model", "rs g8000",
                   "--interface", "xge49", "--iftype", "physical",
                   "--mac", ip.mac, "--ip", ip]
        self.successtest(command)
        self.dsdb_verify()

    def test_200_reject_ip_in_use(self):
        ip = self.net["ut_net_mgmt"].usable[0]
        command = ["add", "network_device", "--network_device", "ipinuse.aqd-unittest.ms.com",
                   "--type", "bor", "--ip", ip,
                   "--interface", "xge49", "--iftype", "physical",
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use" % ip,
                         command)
        self.check_plenary_nonexistant('network_device', 'americas', 'ut',
                                       'ipinuse')
        self.check_plenary_nonexistant('hostdata', 'ipinuse.aqd-unittest.ms.com')

    def test_200_reject_bad_label_implicit(self):
        ip = self.net["ut_net_mgmt"].usable[-1]
        command = ["add", "network_device", "--network_device", "not-alnum.aqd-unittest.ms.com",
                   "--type", "bor", "--ip", ip,
                   "--interface", "xge49", "--iftype", "physical",
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not deduce a valid hardware label",
                         command)
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'not-alnum')
        self.check_plenary_nonexistant('hostdata', 'not-alnum.aqd-unittest.ms.com')

    def test_200_reject_bad_label_explicit(self):
        ip = self.net["ut_net_mgmt"].usable[-1]
        command = ["add", "network_device", "--network_device", "notalnum.aqd-unittest.ms.com",
                   "--label", "not-alnum", "--type", "bor", "--ip", ip,
                   "--interface", "xge49", "--iftype", "physical",
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal hardware label format 'not-alnum'.",
                         command)
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'not-alnum')
        self.check_plenary_nonexistant('hostdata', 'notalnum.aqd-unittest.ms.com')

    # Testing that add network device does not allow a blade....
    def test_200_reject_bad_model(self):
        ip = self.net["ut_net_mgmt"].usable[-1]
        command = ["add", "network_device", "--type", "tor",
                   "--network_device", "badmodel.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "hs21-8853l5u",
                   "--ip", ip, "--interface", "xge49", "--iftype", "physical"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "This command can only be used "
                         "to add network devices.", command)
        self.check_plenary_nonexistant('network_device', 'americas', 'ut',
                                       'badmodel')
        self.check_plenary_nonexistant('hostdata',
                                       'badmodel.aqd-unittest.ms.com')

    def test_205_verify_reject_bad_model(self):
        command = "show network_device --network_device badmodel.aqd-unittest.ms.com"
        out = self.notfoundtest(command.split(" "))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
