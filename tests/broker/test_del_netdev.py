#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014  Contributor
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
"""Module for testing the del network device command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelNetworkDevice(TestBrokerCommand):

    def test_100_del_ut3gd1r01(self):
        # Deprecated usage.
        self.dsdb_expect_delete(self.net["tor_net_12"].usable[0])
        command = "del network_device --network_device ut3gd1r01.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r01')
        self.check_plenary_nonexistant('hostdata', 'ut3gd1r01.aqd-unittest.ms.com')

    def test_101_verify_ut3gd1r01(self):
        # Deprecated usage.
        command = "show network_device --network_device ut3gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_105_del_ut3gd1r04(self):
        self.dsdb_expect_delete(self.net["verari_eth1"].usable[1])
        command = "del network_device --network_device ut3gd1r04.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r04')
        self.check_plenary_nonexistant('hostdata', 'ut3gd1r04.aqd-unittest.ms.com')

    def test_110_del_ut3gd1r05(self):
        ip = self.net["ut_net_mgmt"].usable[0]
        self.dsdb_expect_delete(ip)
        command = "del network_device --network_device ut3gd1r05.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r05')
        self.check_plenary_nonexistant('hostdata', 'ut3gd1r05.aqd-unittest.ms.com')

    def test_115_del_ut3gd1r06(self):
        self.dsdb_expect_delete(self.net["ut_net_mgmt"].usable[4])
        command = "del network_device --network_device ut3gd1r06.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r06')
        self.check_plenary_nonexistant('hostdata', 'ut3gd1r06.aqd-unittest.ms.com')

    def test_120_del_ut3gd1r07(self):
        ip = self.net["ut_net_mgmt"].usable[2]
        self.dsdb_expect_delete(ip)
        command = "del network_device --network_device ut3gd1r07.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r07')
        self.check_plenary_nonexistant('hostdata', 'ut3gd1r07.aqd-unittest.ms.com')

    def test_125_del_switch_in_building(self):
        ip = self.net["ut_net_mgmt"].usable[3]
        self.dsdb_expect_delete(ip)
        command = "del network_device --network_device switchinbuilding.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut',
                                       'switchinbuilding')
        self.check_plenary_nonexistant('hostdata',
                                       'switchinbuilding.aqd-unittest.ms.com')

    def test_130_del_np06bals03(self):
        self.dsdb_expect_delete("172.31.64.69")
        command = "del network_device --network_device np06bals03.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'np06bals03')
        self.check_plenary_nonexistant('hostdata', 'np06bals03.ms.com')

    def test_131_verify_np06bals03(self):
        command = "show network_device --network_device np06bals03.ms.com"
        self.notfoundtest(command.split(" "))

    def test_135_del_np06fals01(self):
        self.dsdb_expect_delete("172.31.88.5")
        command = "del network_device --network_device np06fals01.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'np06fals01')
        self.check_plenary_nonexistant('hostdata', 'np06fals01.ms.com')

    def test_136_verify_np06fals01(self):
        command = "show network_device --network_device np06fals01.ms.com"
        self.notfoundtest(command.split(" "))

    def test_140_del_ut01ga1s02(self):
        self.dsdb_expect_delete(self.net["tor_net_0"].usable[0])
        command = "del network_device --network_device ut01ga1s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga1s02')
        self.check_plenary_nonexistant('hostdata', 'ut01ga1s02.aqd-unittest.ms.com')

    def test_141_verify_ut01ga1s02(self):
        command = "show network_device --network_device ut01ga1s02.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_150_del_ut01ga1s03(self):
        self.dsdb_expect_delete(self.net["hp_eth0"].usable[0])
        command = "del network_device --network_device ut01ga1s03.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga1s03')
        self.check_plenary_nonexistant('hostdata', 'ut01ga1s03.aqd-unittest.ms.com')

    def test_151_verify_ut01ga1s03(self):
        command = "show network_device --network_device ut01ga1s03.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_155_del_ut01ga1s04(self):
        self.dsdb_expect_delete(self.net["verari_eth0"].usable[0])
        command = "del network_device --network_device ut01ga1s04.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga1s04')
        self.check_plenary_nonexistant('hostdata', 'ut01ga1s04.aqd-unittest.ms.com')

    def test_156_verify_ut01ga1s04(self):
        command = "show network_device --network_device ut01ga1s04.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_160_del_ut01ga2s01(self):
        self.dsdb_expect_delete(self.net["vmotion_net"].usable[0])
        command = "del network_device --network_device ut01ga2s01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga2s01')
        self.check_plenary_nonexistant('hostdata', 'ut01ga2s01.aqd-unittest.ms.com')

    def test_165_del_ut01ga2s02(self):
        self.dsdb_expect_delete(self.net["vmotion_net"].usable[1])
        command = "del network_device --network_device ut01ga2s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga2s02')
        self.check_plenary_nonexistant('hostdata', 'ut01ga2s02.aqd-unittest.ms.com')

    def test_170_del_ut01ga2s05(self):
        self.dsdb_expect_delete(self.net["esx_bcp_ut"].usable[0])
        command = "del network_device --network_device ut01ga2s05.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga2s05')
        self.check_plenary_nonexistant('hostdata', 'ut01ga2s05.aqd-unittest.ms.com')

    def test_175_del_np01ga2s05(self):
        self.dsdb_expect_delete(self.net["esx_bcp_np"].usable[0])
        command = "del network_device --network_device np01ga2s05.one-nyp.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'np01ga2s05')
        self.check_plenary_nonexistant('hostdata', 'np01ga2s05.one-nyp.ms.com')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
