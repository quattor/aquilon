#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from netdevtest import VerifyNetworkDeviceMixin


class TestRenameNetworkDevice(TestBrokerCommand, VerifyNetworkDeviceMixin):

    def test_100_rename_ut3gd1r04(self):
        self.dsdb_expect_rename("ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com",
                                "renametest-vlan110-hsrp.aqd-unittest.ms.com")
        self.dsdb_expect_rename("ut3gd1r04-vlan110.aqd-unittest.ms.com",
                                "renametest-vlan110.aqd-unittest.ms.com")
        self.dsdb_expect_rename("ut3gd1r04-loop0.aqd-unittest.ms.com",
                                "renametest-loop0.aqd-unittest.ms.com")
        self.dsdb_expect_rename("ut3gd1r04.aqd-unittest.ms.com",
                                "renametest.aqd-unittest.ms.com")

        self.check_plenary_exists("switchdata", "ut3gd1r04.aqd-unittest.ms.com")
        self.check_plenary_exists('network_device', 'americas', 'ut', 'ut3gd1r04')
        self.check_plenary_exists('hostdata', 'ut3gd1r04.aqd-unittest.ms.com')

        command = ["update", "network_device",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                   "--rename_to", "renametest"]
        self.noouttest(command)

        self.check_plenary_gone("switchdata", "ut3gd1r04.aqd-unittest.ms.com")
        self.check_plenary_gone('network_device', 'americas', 'ut', 'ut3gd1r04')
        self.check_plenary_gone('hostdata', 'ut3gd1r04.aqd-unittest.ms.com')
        self.check_plenary_exists("switchdata", "renametest.aqd-unittest.ms.com")
        self.check_plenary_exists('network_device', 'americas', 'ut', 'renametest')
        self.check_plenary_exists('hostdata', 'renametest.aqd-unittest.ms.com')

        self.dsdb_verify()

    def test_110_verify(self):
        self.verifynetdev("renametest.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net["verari_eth1"].usable[1],
                          mac=self.net["verari_eth1"].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

    def test_200_rename_ut3gd1r04_back(self):
        self.dsdb_expect_rename("renametest-vlan110-hsrp.aqd-unittest.ms.com",
                                "ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com")
        self.dsdb_expect_rename("renametest-vlan110.aqd-unittest.ms.com",
                                "ut3gd1r04-vlan110.aqd-unittest.ms.com")
        self.dsdb_expect_rename("renametest-loop0.aqd-unittest.ms.com",
                                "ut3gd1r04-loop0.aqd-unittest.ms.com")
        self.dsdb_expect_rename("renametest.aqd-unittest.ms.com",
                                "ut3gd1r04.aqd-unittest.ms.com")

        command = ["update", "network_device",
                   "--network_device", "renametest",
                   "--rename_to", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_210_verify(self):
        self.verifynetdev("ut3gd1r04.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net["verari_eth1"].usable[1],
                          mac=self.net["verari_eth1"].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRenameNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
