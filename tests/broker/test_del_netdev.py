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

    def testdelut3gd1r01(self):
        # Deprecated usage.
        self.dsdb_expect_delete(self.net["tor_net_12"].usable[0])
        command = "del network_device --network_device ut3gd1r01.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r01')

    def testverifydelut3gd1r01(self):
        # Deprecated usage.
        command = "show network_device --network_device ut3gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut3gd1r04(self):
        self.dsdb_expect_delete(self.net["verari_eth1"].usable[1])
        command = "del network_device --network_device ut3gd1r04.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r04')

    def testdelut3gd1r05(self):
        self.dsdb_expect_delete(self.net["tor_net_7"].usable[0])
        command = "del network_device --network_device ut3gd1r05.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r05')

    def testdelut3gd1r06(self):
        self.dsdb_expect_delete(self.net["tor_net_8"].usable[1])
        command = "del network_device --network_device ut3gd1r06.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r06')

    def testdelut3gd1r07(self):
        self.dsdb_expect_delete(self.net["tor_net_9"].usable[0])
        command = "del network_device --network_device ut3gd1r07.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r07')

    def testdelut3gd1r08(self):
        self.dsdb_expect_delete(self.net["tor_net_9"].usable[1])
        command = "del network_device --network_device ut3gd1r08.aqd-unittest.ms.com"
        self.successtest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut3gd1r08')

    def testdelnp06bals03(self):
        self.dsdb_expect_delete("172.31.64.69")
        command = "del network_device --network_device np06bals03.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'np06bals03')

    def testverifydelnp06bals03(self):
        command = "show network_device --network_device np06bals03.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp06fals01(self):
        self.dsdb_expect_delete("172.31.88.5")
        command = "del network_device --network_device np06fals01.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'np06fals01')

    def testverifydelnp06fals01(self):
        command = "show network_device --network_device np06fals01.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s02(self):
        self.dsdb_expect_delete(self.net["tor_net_0"].usable[0])
        command = "del network_device --network_device ut01ga1s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga1s02')

    def testverifydelut01ga1s02(self):
        command = "show network_device --network_device ut01ga1s02.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s03(self):
        self.dsdb_expect_delete(self.net["hp_eth0"].usable[0])
        command = "del network_device --network_device ut01ga1s03.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga1s03')

    def testverifydelut01ga1s03(self):
        command = "show network_device --network_device ut01ga1s03.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s04(self):
        self.dsdb_expect_delete(self.net["verari_eth0"].usable[0])
        command = "del network_device --network_device ut01ga1s04.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga1s04')

    def testverifydelut01ga1s04(self):
        command = "show network_device --network_device ut01ga1s04.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga2s01(self):
        self.dsdb_expect_delete(self.net["vmotion_net"].usable[0])
        command = "del network_device --network_device ut01ga2s01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga2s01')

    def testdelut01ga2s02(self):
        self.dsdb_expect_delete(self.net["vmotion_net"].usable[1])
        command = "del network_device --network_device ut01ga2s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga2s02')

    def testdelut01ga2s03(self):
        self.dsdb_expect_delete(self.net["esx_bcp_ut"].usable[0])
        command = "del network_device --network_device ut01ga2s03.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'ut01ga2s03')

    def testdelnp01ga2s03(self):
        self.dsdb_expect_delete(self.net["esx_bcp_np"].usable[0])
        command = "del network_device --network_device np01ga2s03.one-nyp.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()
        self.check_plenary_nonexistant('network_device', 'americas', 'ut', 'np01ga2s03')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
