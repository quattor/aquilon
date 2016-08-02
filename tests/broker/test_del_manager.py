#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2015,2016  Contributor
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
"""Module for testing the del manager command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelManager(TestBrokerCommand):

    def test_100_del_unittest00r(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[4])
        command = "del manager --manager unittest00r.one-nyp.ms.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_105_show_manager(self):
        command = "show manager --manager unittest00r.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_105_show_host(self):
        command = ["show_host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "unittest00r", command)

    def test_105_cat_machine(self):
        command = ["cat", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.matchclean(out, "unittest00r", command)

    def test_110_del_unittest02rsa(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[9])
        command = "del manager --manager unittest02rsa.one-nyp.ms.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_115_verify_unittest02rsa(self):
        command = "show manager --manager unittest02rsa.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_120_del_unittest12r(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[8])
        command = "del manager --manager unittest12r.aqd-unittest.ms.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_125_del_unittest12r(self):
        command = "show manager --manager unittest12r.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def test_200_not_a_manager(self):
        ip = self.net["unknown0"].usable[2]
        command = ["del_manager", "--manager", "unittest00.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com [%s] is not a "
                         "manager." % ip, command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelManager)
    unittest.TextTestRunner(verbosity=2).run(suite)
