#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the del esx cluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


# TODO: merge this into test_del_cluster.py
class TestDelESXCluster(TestBrokerCommand):

    def test_100_del_utecl1(self):
        command = ["del_esx_cluster", "--cluster=utecl1"]
        out = self.statustest(command)
        self.matchoutput(out, "Command del_esx_cluster is deprecated.", command)
        self.check_plenary_gone("cluster", "utecl1", "client",
                                directory_gone=True)
        self.verify_buildfiles("unittest", "clusters/utecl1", want_exist=False,
                               command="del_esx_cluster")

    def test_105_verify_show_utecl1(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        self.notfoundtest(command)

    def test_105_verify_utmc1_members(self):
        command = ["cat", "--metacluster", "utmc1", "--data"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"system/metacluster/members" = list\(\s*'
                          r'"utecl2",\s*'
                          r'"utecl3"\s*'
                          r'\);',
                          command)

    def test_110_del_utmc1(self):
        for i in range(2, 5):
            self.successtest(["del_esx_cluster", "--cluster=utecl%d" % i])

    def test_120_del_utmc4(self):
        for i in range(5, 11):
            command = ["del_esx_cluster", "--cluster=utecl%d" % i]
            self.successtest(command)

    def test_130_del_utmc7(self):
        self.successtest(["del_esx_cluster", "--cluster=utecl11"])

    def test_140_del_sandboxmc(self):
        self.successtest(["del_esx_cluster", "--cluster=sandboxcl1"])

    def test_150_del_utmc8(self):
        self.statustest(["del_cluster", "--cluster", "utecl12"])
        self.statustest(["del_cluster", "--cluster", "utecl13"])

    def test_155_del_utmc9(self):
        self.statustest(["del_cluster", "--cluster", "utecl14"])
        self.statustest(["del_cluster", "--cluster", "utecl15"])

    def test_200_del_nonexistent(self):
        command = ["del_esx_cluster", "--cluster=esx_cluster-does-not-exist"]
        self.notfoundtest(command)

    def test_300_verify_all(self):
        command = ["search_cluster", "--cluster_type", "esx"]
        out = self.commandtest(command)
        self.matchclean(out, "utecl", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
