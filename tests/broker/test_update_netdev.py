#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the update network device command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from netdevtest import VerifyNetworkDeviceMixin


class TestUpdateNetworkDevice(TestBrokerCommand, VerifyNetworkDeviceMixin):

    def test_100_update_ut3gd1r04(self):
        newip = self.net["ut10_eth1"].usable[1]
        self.dsdb_expect_update("ut3gd1r04.aqd-unittest.ms.com", "xge49", newip,
                                comments="Some new switch comments")
        command = ["update", "network_device", "--type", "bor",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                   "--ip", newip, "--model", "uttorswitch",
                   "--comments", "Some new switch comments"]
        self.noouttest(command)
        self.dsdb_verify()
        self.check_plenary_contents('network_device', 'americas', 'ut', 'ut3gd1r04',
                                    contains='uttorswitch')
        self.check_plenary_contents('hostdata', 'ut3gd1r04.aqd-unittest.ms.com',
                                    contains=str(newip))

    def test_105_verify_ut3gd1r04(self):
        self.verifynetdev("ut3gd1r04.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net["ut10_eth1"].usable[1],
                          mac=self.net["ut10_eth1"].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

    def test_110_update_ut3gd1r05(self):
        command = ["update", "network_device",
                   "--network_device", "ut3gd1r05.aqd-unittest.ms.com",
                   "--rack", "ut4", "--model", "uttorswitch",
                   "--vendor", "hp", "--serial", "SNgd1r05_new"]
        self.noouttest(command)
        self.check_plenary_contents('network_device', 'americas', 'ut', 'ut3gd1r05',
                                    contains=['hp', 'SNgd1r05_new', 'uttorswitch'])

    def test_112_update_ut3gd1r05_comment(self):
        self.dsdb_expect_update("ut3gd1r05.aqd-unittest.ms.com",
                                iface="xge49",
                                comments="LANWAN")
        command = ["update", "network_device",
                   "--network_device", "ut3gd1r05.aqd-unittest.ms.com",
                   "--comments", "LANWAN"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_115_verify_ut3gd1r05(self):
        self.verifynetdev("ut3gd1r05.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut4", "a", "4", "SNgd1r05_new", switch_type='tor',
                          ip=self.net["ut_net_mgmt"].usable[0], interface="xge49",
                          comments="LANWAN")

    def test_120_add_interface(self):
        ip = self.net["ut_net_mgmt"].usable[1]
        mac = self.net["ut_net_mgmt"].usable[4].mac
        self.dsdb_expect_update("ut3gd1r06.aqd-unittest.ms.com", "xge49", mac=mac)
        command = ["update_interface", "--network_device=ut3gd1r06.aqd-unittest.ms.com",
                   "--interface=xge49", "--mac", mac]
        self.noouttest(command)
        self.verifynetdev("ut3gd1r06.aqd-unittest.ms.com",
                          "generic", "temp_switch", "ut3", "a", "3",
                          switch_type='tor',
                          ip=ip, mac=mac, interface="xge49")
        self.dsdb_verify()
        self.check_plenary_contents('network_device', 'americas', 'ut', 'ut3gd1r06',
                                    contains=str(mac))

    def test_122_update_with_interface(self):
        newip = self.net["ut_net_mgmt"].usable[4]
        self.dsdb_expect_update("ut3gd1r06.aqd-unittest.ms.com", "xge49", newip)
        command = ["update", "network_device",
                   "--network_device", "ut3gd1r06.aqd-unittest.ms.com",
                   "--ip", newip]
        self.noouttest(command)
        self.dsdb_verify()

    def test_125_verify_ut3gd1r06(self):
        self.verifynetdev("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net["ut_net_mgmt"].usable[4],
                          mac=self.net["ut_net_mgmt"].usable[4].mac,
                          interface="xge49")

    def test_200_update_bad_ip(self):
        ip = self.net["tor_net_12"].usable[0]
        command = ["update", "network_device", "--ip", ip,
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by physical "
                         "interface xge49 of switch "
                         "ut3gd1r01.aqd-unittest.ms.com." % ip,
                         command)

    def test_205_update_netdev_in_chassis_slot(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com",
                   "--slot", "2"]
        self.successtest(command)
        command = ["show", "chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Slot #1 (type: network_device): Empty",
                         command)
        self.matchoutput(out,
                         "Slot #2 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)

    def test_210_update_netdev_in_chassis_slot(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com",
                   "--slot", "3", "--multislot"]
        self.successtest(command)
        command = ["show", "chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Slot #1 (type: network_device): Empty",
                         command)
        self.matchoutput(out,
                         "Slot #2 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)
        self.matchoutput(out,
                         "Slot #3 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)

    def test_215_update_netdev_in_chassis_slot(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com", "--chassis",
                   "ut3c1", "--slot", "1", "--multislot"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network Device cannot be in multiple chassis. "
                         "Use --clearchassis to remove current chassis slot information.",
                         command)
        command = ["show", "chassis", "--chassis", "ut3c1"]
        out = self.commandtest(command)
        self.matchclean(out,
                         "Slot #1 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)

    def test_220_update_netdev_in_chassis_slot(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com", "--chassis",
                   "ut3c1", "--slot", "1", "--clearchassis"]
        self.successtest(command)
        command = ["show", "chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        for i in range(2):
            self.matchoutput(out,
                             "Slot #{} (type: network_device): Empty".format(i+1),
                             command)
        command = ["show", "chassis", "--chassis", "ut3c1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                        "Slot #1 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                        command)

    def test_225_update_netdev_in_chassis_chassis(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com", "--chassis",
                   "ut3c5", "--slot", "1"]
        self.successtest(command)
        command = ["show", "chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Slot #1 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)

    def test_230_update_netdev_in_chassis_chassis(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com", "--slot", "2", "--multislot"]
        self.successtest(command)
        command = ["show", "chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Slot #1 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)
        self.matchoutput(out,
                         "Slot #2 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)",
                         command)
        self.matchoutput(out,
                         "Slot #3 (type: network_device): Empty",
                         command)
        command = ["show", "chassis", "--chassis", "ut3c1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Slot #1 (type: network_device): Empty",
                         command)

    def test_235_update_netdev_in_chassis_chassis(self):
        command = ["update", "network_device", "--network_device",
                   "ut3c5netdev1.aqd-unittest.ms.com", "--chassis", "ut3c5", "--slot", "5", "--multislot"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Chassis ut3c5.aqd-unittest.ms.com "
                              "slot 5 already has network device ut3c5netdev2", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
