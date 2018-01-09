#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2015,2016,2017  Contributor
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


class TestDelChassis(TestBrokerCommand):
    def test_100_del_ut3c5_used(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[6])
        command = "del chassis --chassis ut3c5.aqd-unittest.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Chassis ut3c5.aqd-unittest.ms.com is "
                              "still in use by 3 machines or network devices. "
                              "Use --clear_slots if you really want to delete it.",
                         command.split(" "))

    def test_101_del_ut3c5(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[6])
        command = "del chassis --chassis ut3c5.aqd-unittest.ms.com --clear_slots"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_105_verify_ut3c5(self):
        command = "show chassis --chassis ut3c5.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_106_del_ut3c5_again(self):
        command = ["del_chassis", "--chassis", "ut3c5.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DnsRecord ut3c5.aqd-unittest.ms.com, "
                         "DNS environment internal not found.",
                         command)

    def test_110_del_ut3c1(self):
        command = "del chassis --chassis ut3c1.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def test_115_verify_ut3c1(self):
        command = "show chassis --chassis ut3c1.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_120_del_ut9_chassis(self):
        for i in range(1, 8):
            self.dsdb_expect_delete(self.net["ut9_chassis"].usable[i])
            command = "del chassis --chassis ut9c%d.aqd-unittest.ms.com" % i
            self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_125_verify_ut9_chassis(self):
        for i in range(1, 6):
            command = "show chassis --chassis ut9c%d.aqd-unittest.ms.com" % i
            self.notfoundtest(command.split(" "))

    def test_130_del_np3c5(self):
        self.noouttest(["del_chassis", "--chassis", "np3c5.one-nyp.ms.com"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
