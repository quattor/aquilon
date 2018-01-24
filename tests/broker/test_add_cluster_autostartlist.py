#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017,2018  Contributor
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
"""Module for testing the add cluster autostartlist command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddClusterAutoStartList(TestBrokerCommand):

    def test_100_add_rg_single_host_range_lo(self):
        command = ["add_cluster_autostartlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--hostname", "utbhost04.aqd-unittest.ms.com",
                   "--order", -99]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Value for order (-99) is outside of the configured range 1..99",
                         command)

    def test_100_add_rg_single_host_range_hi(self):
        command = ["add_cluster_autostartlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--hostname", "utbhost04.aqd-unittest.ms.com",
                   "--order", 255]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Value for order (255) is outside of the configured range 1..99",
                         command)

    def test_102_add_rg_single_host(self):
        self.noouttest(["add_cluster_autostartlist", "--cluster", "utbvcs1b",
                        "--resourcegroup", "utbvcs1bas01",
                        "--hostname", "utbhost04.aqd-unittest.ms.com",
                        "--order", 1])
        self.noouttest(["add_cluster_autostartlist", "--cluster", "utbvcs1b",
                        "--resourcegroup", "utbvcs1bas02",
                        "--hostname", "utbhost03.aqd-unittest.ms.com",
                        "--order", 1])

    def test_103_show_cluster_autostartlist_cluster(self):
        command = ["show_cluster_autostartlist", "--cluster", "utbvcs1b"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'\s*Resource Group: utbvcs1bas01\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost04.aqd-unittest.ms.com Order: 1$',
                          command)


    def test_103_show_cluster_autostartlist_all(self):
        command = ["show_cluster_autostartlist", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'High Availability Cluster: utbvcs1b',
                         command)
        self.searchoutput(out,
                         r'\s*Resource Group: utbvcs1bas01\s*'
                         r'AutoStartList\s*'
                         r'Member: utbhost04.aqd-unittest.ms.com Order: 1\s*',
                          command)
        self.searchoutput(out,
                          r'\s*Resource Group: utbvcs1bas02\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost03.aqd-unittest.ms.com Order: 1$',
                          command)

    def test_105_cat_utbvcs1b(self):
        command = ["cat", "--cluster", "utbvcs1b", "--resourcegroup", "utbvcs1bas01"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"resources/auto_start_list" = append(create("resource/cluster/utbvcs1b/resourcegroup/utbvcs1bas01/auto_start_list/auto_start_list/config"));',
                         command)

        command = ["cat", "--cluster", "utbvcs1b", "--resourcegroup", "utbvcs1bas01",
                   "--auto_start_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = list\(\s*'
                          r'"utbhost04.aqd-unittest.ms.com"\s*'
                          r'\);$',
                          command)

        command = ["cat", "--cluster", "utbvcs1b", "--resourcegroup", "utbvcs1bas02",
                   "--auto_start_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = list\(\s*'
                          r'"utbhost03.aqd-unittest.ms.com"\s*'
                          r'\);$',
                          command)

    def test_105_show_utbvcs1b(self):
        command = ["show_cluster", "--cluster", "utbvcs1b"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Resource Group: utbvcs1bas01\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost04.aqd-unittest.ms.com Order: 1$',
                          command)
        self.searchoutput(out,
                          r'Resource Group: utbvcs1bas02\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost03.aqd-unittest.ms.com Order: 1$',
                          command)

    def test_105_show_utbvcs1b_proto(self):
        command = ["show_cluster", "--cluster", "utbvcs1b", "--format", "proto"]
        cluster = self.protobuftest(command, expect=1)[0]
        found = set()
        for rg in cluster.resources:
            if rg.type != "resourcegroup":
                continue
            found.add(rg.name)
            for resource in rg.resourcegroup.resources:
                if resource.type != "auto_start_list":
                    continue
                self.assertEqual(len(resource.autostartlist), 1)
                self.assertEqual(resource.autostartlist[0].cluster, "utbvcs1b")
                self.assertEqual(resource.autostartlist[0].rg, rg.name)
                self.assertEqual(resource.autostartlist[0].order_idx, 1)
                if rg.name == "utbvcs1bas01":
                    self.assertEqual(resource.autostartlist[0].member,
                                     "utbhost04.aqd-unittest.ms.com")
                else:
                    self.assertEqual(resource.autostartlist[0].member,
                                     "utbhost03.aqd-unittest.ms.com")

        self.assertEqual(found, set(["utbvcs1bas01", "utbvcs1bas02"]))

    def test_110_cluster_default(self):
        self.noouttest(["add_cluster_autostartlist", "--cluster", "utbvcs1d",
                        "--hostname", "utbhost07.aqd-unittest.ms.com",
                        "--order", 5])
        self.noouttest(["add_cluster_autostartlist", "--cluster", "utbvcs1d",
                        "--hostname", "utbhost08.aqd-unittest.ms.com",
                        "--order", 10])

    def test_111_rg_override(self):
        # CamelCase
        self.noouttest(["add_cluster_autostartlist", "--cluster", "utbvcs1d",
                        "--resourcegroup", "UTBvcs1das01",
                        "--hostname", "UTBhost07.aqd-unittest.ms.com",
                        "--order", 20])
        # CamelCase
        self.noouttest(["add_cluster_autostartlist", "--cluster", "utbvcs1d",
                        "--resourcegroup", "UTBvcs1das01",
                        "--hostname", "UTBhost08.aqd-unittest.ms.com",
                        "--order", 15])
        self.check_plenary_exists("resource", "cluster", "utbvcs1d",
                                  "resourcegroup", "utbvcs1das01",
                                  "auto_start_list", "auto_start_list", "config")

    def test_115_show_utbvcs1d(self):
        command = ["show_cluster", "--cluster", "utbvcs1d"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Resources:\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost07.aqd-unittest.ms.com Order: 5\s*'
                          r'Member: utbhost08.aqd-unittest.ms.com Order: 10\s*',
                          command)
        self.searchoutput(out,
                          r'Resource Group: utbvcs1das01\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost08.aqd-unittest.ms.com Order: 15\s*'
                          r'Member: utbhost07.aqd-unittest.ms.com Order: 20\s*',
                          command)

    def test_115_show_utbvcs1d_proto(self):
        command = ["show_cluster", "--cluster", "utbvcs1d", "--format", "proto"]
        cluster = self.protobuftest(command, expect=1)[0]
        found_cluster_default = False
        found_rg_override = False
        for resource in cluster.resources:
            if resource.type == "auto_start_list":
                found_cluster_default = True
                self.assertEqual(len(resource.autostartlist), 2)
                self.assertEqual(resource.autostartlist[0].cluster, "utbvcs1d")
                self.assertEqual(resource.autostartlist[1].cluster, "utbvcs1d")
                self.assertEqual(resource.autostartlist[0].rg, "")
                self.assertEqual(resource.autostartlist[1].rg, "")
                hosts = {asl.member: asl.order_idx
                         for asl in resource.autostartlist}
                self.assertEqual(hosts, {'utbhost07.aqd-unittest.ms.com': 5,
                                         'utbhost08.aqd-unittest.ms.com': 10})
            if resource.type == "resourcegroup" and resource.name == "utbvcs1das01":
                for res2 in resource.resourcegroup.resources:
                    if res2.type != "auto_start_list":
                        continue
                    found_rg_override = True
                    self.assertEqual(len(res2.autostartlist), 2)
                    hosts = {asl.member: asl.order_idx
                             for asl in res2.autostartlist}
                    self.assertEqual(hosts, {'utbhost08.aqd-unittest.ms.com': 15,
                                             'utbhost07.aqd-unittest.ms.com': 20})

        self.assertTrue(found_cluster_default,
                        "cluster default settings not found")
        self.assertTrue(found_rg_override,
                        "resourcegroup override not found")

    def test_115_cat_utbvcs1d(self):
        command = ["cat", "--cluster", "utbvcs1d", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/resources/auto_start_list" =',
                         command)

        command = ["cat", "--cluster", "utbvcs1d", "--auto_start_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = list\(\s*'
                          r'"utbhost07.aqd-unittest.ms.com",\s*'
                          r'"utbhost08.aqd-unittest.ms.com"\s*'
                          r'\);',
                          command)

        command = ["cat", "--cluster", "utbvcs1d", "--resourcegroup",
                   "utbvcs1das01", "--auto_start_list"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"members" = list\(\s*'
                          r'"utbhost08.aqd-unittest.ms.com",\s*'
                          r'"utbhost07.aqd-unittest.ms.com"\s*'
                          r'\);',
                          command)

        command = ["cat", "--cluster", "utbvcs1d", "--resourcegroup",
                   "utbvcs1das02", "--auto_start_list"]
        self.notfoundtest(command)

    def test_120_show_cluster_autostartlist_cluster(self):
        command = ["show_cluster_autostartlist", "--cluster", "utbvcs1d"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'High Availability Cluster: utbvcs1d\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost07.aqd-unittest.ms.com Order: 5\s*'
                          r'Member: utbhost08.aqd-unittest.ms.com Order: 10\s*',
                          command)

    def test_120_show_cluster_autostartlist_all(self):
        command = ["show_cluster_autostartlist", "--all"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'High Availability Cluster: utbvcs1d\s*'
                          r'AutoStartList\s*'
                          r'Member: utbhost07.aqd-unittest.ms.com Order: 5\s*'
                          r'Member: utbhost08.aqd-unittest.ms.com Order: 10\s*',
                          command)

    def test_200_no_member(self):
        command = ["add_cluster_autostartlist", "--cluster", "utbvcs1b",
                   "--hostname", "server1.aqd-unittest.ms.com", "--order", 1]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host server1.aqd-unittest.ms.com is not a member of "
                         "high availability cluster utbvcs1b.",
                         command)

    def test_200_add_again(self):
        command = ["add_cluster_autostartlist", "--cluster", "utbvcs1b",
                   "--resourcegroup", "utbvcs1bas01",
                   "--hostname", "utbhost04.aqd-unittest.ms.com",
                   "--order", 10]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Host utbhost04.aqd-unittest.ms.com already has "
                         "a(n) AutoStartList entry.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddClusterAutoStartList)
    unittest.TextTestRunner(verbosity=2).run(suite)
