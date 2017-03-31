#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017  Contributor
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
"""Module for testing the del cluster systemlist command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelClusterSystemList(TestBrokerCommand):

    def test_100_del_rg_single_host(self):
        self.noouttest(["del_cluster_systemlist", "--cluster", "utbvcs1b",
                        "--resourcegroup", "utbvcs1bas01",
                        "--hostname", "utbhost04.aqd-unittest.ms.com"])

    def test_105_cat_utbvcs1b(self):
        command = ["cat", "--cluster", "utbvcs1b", "--resourcegroup", "utbvcs1bas01"]
        out = self.commandtest(command)
        self.matchclean(out, "system_list", command)

    def test_105_show_utbvcs1b(self):
        command = ["show_cluster", "--cluster", "utbvcs1b"]
        out = self.commandtest(command)
        self.matchclean(out, "Member: utbhost04.aqd-unittest.ms.com Priority:", command)

    def test_110_cluster_default_all(self):
        path = ["resource", "cluster", "utbvcs1d",
                "system_list", "system_list", "config"]
        self.check_plenary_exists(*path)
        self.noouttest(["del_cluster_systemlist", "--cluster", "utbvcs1d", "--all"])
        self.check_plenary_gone(*path)

    def test_111_rg_override(self):
        path = ["resource", "cluster", "utbvcs1d",
                "resourcegroup", "utbvcs1das01",
                "system_list", "system_list", "config"]
        self.check_plenary_exists(*path)
        self.noouttest(["del_cluster_systemlist", "--cluster", "utbvcs1d",
                        "--resourcegroup", "utbvcs1das01",
                        "--hostname", "utbhost07.aqd-unittest.ms.com"])
        self.check_plenary_exists(*path)
        self.noouttest(["del_cluster_systemlist", "--cluster", "utbvcs1d",
                        "--resourcegroup", "utbvcs1das01",
                        "--hostname", "utbhost08.aqd-unittest.ms.com"])
        self.check_plenary_gone(*path)

    def test_115_show_utbvcs1d(self):
        command = ["show_cluster", "--cluster", "utbvcs1d"]
        out = self.commandtest(command)
        self.matchclean(out, "SystemList", command)

    def test_115_cat_utbvcs1d(self):
        command = ["cat", "--cluster", "utbvcs1d", "--data"]
        out = self.commandtest(command)
        self.matchclean(out, "system_list", command)

        command = ["cat", "--cluster", "utbvcs1d", "--system_list"]
        self.notfoundtest(command)
        self.matchclean(out, "system_list", command)

        command = ["cat", "--cluster", "utbvcs1d", "--resourcegroup",
                   "utbvcs1das01", "--system_list"]
        self.notfoundtest(command)

    def test_200_del_again(self):
        command = ["del_cluster_systemlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--hostname", "utbhost04.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SystemList system_list, "
                         "resource group utbvcs1bas01 not found.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelClusterSystemList)
    unittest.TextTestRunner(verbosity=2).run(suite)
