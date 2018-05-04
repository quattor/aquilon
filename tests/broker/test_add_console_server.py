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
"""Module for testing the add chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from consoleservertest import VerifyConsoleServerMixin

class TestAddConsoleServer(TestBrokerCommand, VerifyConsoleServerMixin):
    def test_100_add_utcs01(self):
        ip = self.net["ut9_conservers"].usable[1]
        self.dsdb_expect_add("utcs01.aqd-unittest.ms.com", ip, "mgmt", ip.mac, comments="Some console server comments")
        command = ["add", "console_server", "--console_server", "utcs01.aqd-unittest.ms.com",
                   "--rack", "ut9", "--model", "utconserver",
                   "--serial", "ABC12345", "--comments", "Some console server comments",
                   "--ip", ip, "--mac", ip.mac]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_verify_utcs01(self):
        ip = self.net["ut9_conservers"].usable[1]
        self.verifyconsoleserver("utcs01.aqd-unittest.ms.com", "aurora_vendor",
                           "utconserver", "ut9", "g", "3", "ABC12345",
                           ip, ip.mac, comments="Some console server comments")

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


    def test_120_add_more_console_server(self):
        for i in range(2, 8):
            ip = self.net["ut9_conservers"].usable[i]
            self.dsdb_expect_add("ut9csa%d.aqd-unittest.ms.com" % i,
                                 ip, "mgmt", ip.mac)
            command = ["add", "console_server",
                       "--console_server", "ut9csa%d.aqd-unittest.ms.com" % i,
                       "--rack", "ut9", "--model", "utconserver",
                       "--ip", ip, "--mac", ip.mac]
            self.noouttest(command)
        self.dsdb_verify()

    def test_125_verify_ut9_console_server(self):
        for i in range(2, 6):
            self.verifyconsoleserver("ut9csa%d.aqd-unittest.ms.com" % i,
                               "aurora_vendor", "utconserver", "ut9", "", "",
                               ip=str(self.net["ut9_conservers"].usable[i]),
                               mac=self.net["ut9_conservers"].usable[i].mac,
                               interface="mgmt")

    def test_300_verifyconsoleserverall(self):
        command = ["show", "console_server", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "utcs01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut9csa2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut9csa4.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut9csa6.aqd-unittest.ms.com", command)

#    def test_305_show_console_server_all_proto(self):
#        command = ["show", "console_server", "--all", "--format", "proto"]
#        console_server_list = self.protobuftest(command, expect=10)
#
#        # Verify that the console server that were created in the previous
#        # methods of this class are in the protobuf dump too
#        search_console_server_primary_name = set([
#            'utcs01.aqd-unittest.ms.com',
#            'ut9csa3.aqd-unittest.ms.com',
#            'ut9csa5.aqd-unittest.ms.com',
#            'ut9csa7.aqd-unittest.ms.com',
#        ])
#        for console_server in console_server_list:
#            search_console_server_primary_name.discard(console_server.primary_name)
#
#        self.assertFalse(
#            search_console_server_primary_name,
#            'The following chassis have not been found in the protobuf '
#            'output: {}'.format(', '.join(search_console_server_primary_name)))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
