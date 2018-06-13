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
"""Module for testing the del chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelConsoleServer(TestBrokerCommand):
    def test_100_del_utcs01_used(self):
        self.dsdb_expect_delete(self.net["unknown2"].usable[1])
        command = "del console_server --console_server utcs01.aqd-unittest.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Console Server utcs01.aqd-unittest.ms.com "
                              "is still in use.  Specify --clear_ports if you really "
                              "want to delete it.",
                         command.split(" "))

    def test_101_del_utcs01(self):
        self.dsdb_expect_delete(self.net["unknown2"].usable[1])
        command = "del console_server --console_server utcs01.aqd-unittest.ms.com --clear_ports"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_105_verify_utcs01(self):
        command = "show console_server --console_server utcs01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_106_del_utcs01_again(self):
        command = ["del_console_server", "--console_server", "utcs01.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DnsRecord utcs01.aqd-unittest.ms.com, "
                         "DNS environment internal not found.",
                         command)


    def test_120_del_ut9_console_servers(self):
        for i in range(2, 8):
            self.dsdb_expect_delete(self.net["ut9_conservers"].usable[i])
            command = "del console_server --console_server ut9csa%d.aqd-unittest.ms.com" % i
            self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_125_verify_ut9_chassis(self):
        for i in range(2, 6):
            command = "show console_server --console_server ut9csa%d.aqd-unittest.ms.com" % i
            self.notfoundtest(command.split(" "))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
