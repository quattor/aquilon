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
"""Module for testing the update chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from consoleservertest import VerifyConsoleServerMixin


class TestUpdateConsoleServer(TestBrokerCommand, VerifyConsoleServerMixin):

    def test_100_update_ut9csa2(self):
        ip = self.net["unknown2"].usable[1]
        self.dsdb_expect_update("utcs01.aqd-unittest.ms.com", "mgmt", ip,
                             comments="Some new console server comments")
        command = ["update", "console_server", "--console_server", "utcs01.aqd-unittest.ms.com",
                   "--rack", "ut3", "--serial", "ABC5678",
                   "--model", "utconserver", "--ip", ip,
                   "--comments", "Some new console server comments"]
        self.noouttest(command)

    def test_110_verify_ut9csa2(self):
        self.verifyconsoleserver("utcs01.aqd-unittest.ms.com", "aurora_vendor", "utconserver",
                           "ut3", "a", "3", "ABC5678",
                           comments="Some new console server comments",
                           ip=self.net["unknown2"].usable[1],
                           mac=self.net["ut9_conservers"].usable[1].mac)

    def test_200_update_bad_ip(self):
        ip = self.net["unknown2"].usable[1]
        command = ["update", "console_server", "--ip", ip,
                   "--console_server", "ut9csa3.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by on-board admin "
                         "interface mgmt of console server "
                         "utcs01.aqd-unittest.ms.com." % ip,
                         command)

    def test_200_update_bad_model(self):
        command = ["update", "console_server", "--model", "uttorswitch",
                   "--console_server", "ut9csa2.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Not Found: Model uttorswitch, model_type console_server not found.",
                         command)

    def test_200_not_console_server(self):
        command = ["update", "console_server", "--console_server",
                   "ut3gd1r01.aqd-unittest.ms.com",
                   "--comments", "Not a console server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Switch ut3gd1r01.aqd-unittest.ms.com exists, but "
                         "is not a console server.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
