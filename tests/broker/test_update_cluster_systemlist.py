#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
"""Module for testing the update cluster systemlist command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateClusterSystemList(TestBrokerCommand):

    def test_100_update_rg_single_host(self):
        self.noouttest(["update_cluster_systemlist", "--cluster", "utbvcs1b",
                        "--resourcegroup", "utbvcs1bas01",
                        "--member", "utbhost04.aqd-unittest.ms.com",
                        "--priority", 2])

    def test_100_update_rg_single_host_range_lo(self):
        command = ["update_cluster_systemlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--member", "utbhost04.aqd-unittest.ms.com",
                   "--priority", 0]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Value for priority (0) is outside of the configured range 1..99",
                         command)

    def test_100_update_rg_single_host_range_hi(self):
        command = ["update_cluster_systemlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--member", "utbhost04.aqd-unittest.ms.com",
                   "--priority", 100]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Value for priority (100) is outside of the configured range 1..99",
                         command)

    def test_105_cat_utbvcs1b(self):
        command = ["cat", "--cluster", "utbvcs1b", "--resourcegroup", "utbvcs1bas01",
                   "--system_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = nlist\(\s*'
                          r'"utbhost04.aqd-unittest.ms.com", 2\s*'
                          r'\);$',
                          command)

    def test_105_show_utbvcs1b(self):
        command = ["show_cluster", "--cluster", "utbvcs1b"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Resource Group: utbvcs1bas01\s*'
                          r'(^      .*$\n)+'
                          r'^      SystemList\s*'
                          r'Member: utbhost04.aqd-unittest.ms.com Priority: 2$',
                          command)
        self.searchoutput(out,
                          r'Resource Group: utbvcs1bas02\s*'
                          r'(^      .*$\n)+'
                          r'^      SystemList\s*'
                          r'Member: utbhost03.aqd-unittest.ms.com Priority: 1$',
                          command)

    def test_110_update_cluster_default(self):
        self.noouttest(["update_cluster_systemlist", "--cluster", "utbvcs1d",
                        "--member", "utbhost07.aqd-unittest.ms.com",
                        "--priority", 25])

    def test_111_rg_override(self):
        # CamelCase
        self.noouttest(["update_cluster_systemlist", "--cluster", "utbvcs1d",
                        "--resourcegroup", "UTBvcs1das01",
                        "--member", "UTBhost07.aqd-unittest.ms.com",
                        "--priority", 10])

    def test_115_show_utbvcs1d(self):
        command = ["show_cluster", "--cluster", "utbvcs1d"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'^    SystemList\s*'
                          r'Member: utbhost08.aqd-unittest.ms.com Priority: 10\s*'
                          r'Member: utbhost07.aqd-unittest.ms.com Priority: 25\s*',
                          command)
        self.searchoutput(out,
                          r'Resource Group: utbvcs1das01\s*'
                          r'(^      .*$\n)+'
                          r'^      SystemList\s*'
                          r'Member: utbhost07.aqd-unittest.ms.com Priority: 10\s*'
                          r'Member: utbhost08.aqd-unittest.ms.com Priority: 15\s*',
                          command)

    def test_115_cat_utbvcs1d(self):
        command = ["cat", "--cluster", "utbvcs1d", "--system_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = nlist\(\s*'
                          r'"utbhost07.aqd-unittest.ms.com", 25,\s*'
                          r'"utbhost08.aqd-unittest.ms.com", 10\s*'
                          r'\);',
                          command)

        command = ["cat", "--cluster", "utbvcs1d", "--resourcegroup",
                   "utbvcs1das01", "--system_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = nlist\(\s*'
                          r'"utbhost07.aqd-unittest.ms.com", 10,\s*'
                          r'"utbhost08.aqd-unittest.ms.com", 15\s*'
                          r'\);',
                          command)

    def test_200_no_member(self):
        command = ["update_cluster_systemlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--member", "server1.aqd-unittest.ms.com", "--priority", 1]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host server1.aqd-unittest.ms.com does not have "
                         "a SystemList entry.",
                         command)

    def test_200_no_asl(self):
        command = ["update_cluster_systemlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--member", "utbhost03.aqd-unittest.ms.com", "--priority", 1]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host utbhost03.aqd-unittest.ms.com does not have "
                         "a SystemList entry.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateClusterSystemList)
    unittest.TextTestRunner(verbosity=2).run(suite)
