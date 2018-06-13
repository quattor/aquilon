#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Module for testing the bind console server command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from consoleservertest import VerifyConsoleServerMixin
from netdevtest import VerifyNetworkDeviceMixin

class TestBindConsoleServer(TestBrokerCommand, VerifyConsoleServerMixin, VerifyNetworkDeviceMixin):
    def test_100_bind_utcs01(self):
        command = ["bind", "console_server", "--console_server", "utcs01.aqd-unittest.ms.com",
                   "--console_port", "5001", "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_105_verify_utcs01(self):
        ip = self.net["unknown2"].usable[1]
        mac = self.net["ut9_conservers"].usable[1].mac
        self.verifyconsoleserver("utcs01.aqd-unittest.ms.com", "aurora_vendor",
                           "utconserver", "ut3", "b", "3", "ABC5678",
                           ip, mac, comments="Some new console server comments", ports=[(5001, 'Switch', 'ut3gd1r04.aqd-unittest.ms.com'),])

#    def test_106_show_utc01_proto(self):
#        command = ["show", "console_server", "--console_server", "utcs01.aqd-unittest.ms.com",
#                   "--format", "proto"]
#        console_server = self.protobuftest(command, expect=1)[0]
#
#        self.assertEqual(console_server.name, 'utcs01')
#        self.assertEqual(console_server.primary_name, 'utcs01.aqd-unittest.ms.com')
#        self.assertEqual(console_server.serial_no, 'ABC12345')
#
#        self.assertEqual(console_server.model.model_type, 'console_server')
#        self.assertEqual(console_server.model.name, 'utconserver')
#        self.assertEqual(console_server.model.vendor, 'aurora_vendor')
#
#        self.assertEqual(console_server.location.location_type, 'rack')
#        self.assertEqual(console_server.location.name, 'np3')
#        self.assertEqual(console_Server.location.fullname, 'np3bad')
#        self.assertEqual(console_server.location.col, '3')
#        self.assertEqual(console_server.location.row, 'a')
#
#        self.assertEqual(len(console_server.slots), 0)
#
#        self.assertEqual(len(console_server.interfaces), 1)

    def test_200_port_cannot_be_allocated_twice(self):
        command = ["bind", "console_server", "--console_server", "utcs01.aqd-unittest.ms.com",
                   "--console_port", "5001", "--network_device", "ut3gd1r06.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Port 5001 is already in use by switch ut3gd1r04.aqd-unittest.ms.com.",
                         command)

    def test_300_bind_ut9csa2(self):
        command = ["bind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5001", "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_301_bind_ut9csa2(self):
        command = ["bind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5002", "--network_device", "ut3gd1r05.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_302_verify_utcs01(self):
        ip = self.net["ut9_conservers"].usable[2]
        mac = self.net["ut9_conservers"].usable[2].mac
        self.verifyconsoleserver("ut9csa2.aqd-unittest.ms.com", "aurora_vendor",
                           "utconserver", "ut9", "h", "9", None,
                           ip, mac, ports=[(5001, 'Switch', 'ut3gd1r01.aqd-unittest.ms.com'),
                                           (5002, 'Switch', 'ut3gd1r05.aqd-unittest.ms.com')])

    def test_303_verify_ut3gd1r01(self):
        ip = self.net["tor_net_12"].usable[0]

        self.verifynetdev("ut3gd1r01.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "b", "3", "SNgd1r01", switch_type='bor', ip=ip,
                          interface="xge49")

    def test_305_unbind_by_port(self):
        command = ["unbind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5001"]
        self.noouttest(command)

    def test_306_unbind_by_client(self):
        command = ["unbind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--network_device", "ut3gd1r05.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_307_unbind_wrong_client(self):
        command = ["unbind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Switch ut3gd1r04.aqd-unittest.ms.com is not bound to console server "
                         "ut9csa2.aqd-unittest.ms.com.",
                         command)

    def test_308_unbind_unused_port(self):
        command= ["unbind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5003"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Port 5003 is not used.",
                         command)

    def test_400_bind_machine_ut3c5n10(self):
        command = ["bind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5011", "--machine", "ut3c5n10"]
        self.noouttest(command)

    def test_401_bind_machine_ut3c5n3(self):
        command = ["bind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5012", "--machine", "ut3c5n3"]
        self.noouttest(command)

    def test_402_verify_utcs01(self):
        ip = self.net["ut9_conservers"].usable[2]
        mac = self.net["ut9_conservers"].usable[2].mac
        self.verifyconsoleserver("ut9csa2.aqd-unittest.ms.com", "aurora_vendor",
                           "utconserver", "ut9", "h", "9", None,
                           ip, mac, ports=[(5011, 'Machine', 'unittest02.one-nyp.ms.com'),
                                           (5012, 'Machine', 'unittest21.aqd-unittest.ms.com')])

    def test_403_unbind_by_port(self):
        command = ["unbind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--console_port", "5011"]
        self.noouttest(command)

    def test_404_unbind_by_client(self):
        command = ["unbind", "console_server", "--console_server", "ut9csa2.aqd-unittest.ms.com",
                   "--machine", "ut3c5n3"]
        self.noouttest(command)

    #This host will be unbind at del_console_server
    def test_501_bind_machine_ut3c5n2(self):
        command = ["bind", "console_server", "--console_server", "utcs01.aqd-unittest.ms.com",
                   "--console_port", "5022", "--machine", "ut3c5n2"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
