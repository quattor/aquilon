#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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
"""Module for testing how a HA cluster might be configured."""

import os.path

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUsecaseHACluster(TestBrokerCommand):

    def test_100_add_hacl1(self):
        command = ["add", "cluster", "--cluster", "hacl1", "--campus", "ny",
                   "--down_hosts_threshold", 0, "--archetype", "hacluster",
                   "--sandbox", "%s/utsandbox" % self.user,
                   "--personality", "hapersonality"]
        self.noouttest(command)

    def test_105_verify_hacl1_location(self):
        command = ["show_cluster", "--cluster", "hacl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Campus: ny", command)
        self.matchclean(out, "Building:", command)
        self.matchclean(out, "Rack:", command)

    def test_110_add_hacl2(self):
        command = ["add", "cluster", "--cluster", "hacl2", "--campus", "ny",
                   "--down_hosts_threshold", 0, "--archetype", "hacluster",
                   "--max_members", 2,
                   "--sandbox", "%s/utsandbox" % self.user,
                   "--personality", "hapersonality"]
        self.noouttest(command)

    def test_120_add_members(self):
        for i in range(0, 4):
            server_idx = i + 2
            cluster_idx = (i % 2) + 1
            self.successtest(["cluster", "--cluster", "hacl%d" % cluster_idx,
                              "--hostname", "server%d.aqd-unittest.ms.com" %
                              server_idx])

    def test_121_fix_hacl1_location(self):
        self.noouttest(["update_cluster", "--cluster", "hacl1",
                        "--fix_location"])

    def test_122_verify_hacl1_location(self):
        command = ["show_cluster", "--cluster", "hacl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut9", command)

    def test_125_add_cluster_srv(self):
        ip1 = self.net["unknown0"].usable[26]
        ip2 = self.net["unknown0"].usable[27]
        self.dsdb_expect_add("hacl1.aqd-unittest.ms.com", ip1)
        self.statustest(["add", "service", "address",
                         "--shortname", "hacl1",
                         "--name", "hacl1", "--cluster", "hacl1",
                         "--ip", ip1])

        self.dsdb_expect_add("hacl2.new-york.ms.com", ip2)
        self.statustest(["add", "service", "address",
                         "--shortname", "hacl2",
                         "--name", "hacl2", "--cluster", "hacl2",
                         "--ip", ip2])
        self.dsdb_verify()

    def test_130_add_resourcegroups(self):
        for cl in range(1, 3):
            for rg in range(1, 3):
                self.successtest(["add", "resourcegroup",
                                  "--cluster", "hacl%d" % cl,
                                  "--resourcegroup", "hacl%dg%d" % (cl, rg)])
                self.check_plenary_exists("resource",
                                          "cluster", "hacl%d" % cl,
                                          "resourcegroup", "hacl%dg%d" % (cl, rg),
                                          "config")

    def test_135_add_apps(self):
        for cl in range(1, 3):
            for rg in range(1, 3):
                self.noouttest(["add", "application",
                                "--cluster", "hacl%d" % cl,
                                "--resourcegroup", "hacl%dg%d" % (cl, rg),
                                "--application", "hacl%dg%dapp" % (cl, rg),
                                "--eon_id", 2])
                self.check_plenary_exists("resource",
                                          "cluster", "hacl%d" % cl,
                                          "resourcegroup", "hacl%dg%d" % (cl, rg),
                                          "application", "hacl%dg%dapp" % (cl, rg),
                                          "config")

    def test_135_add_fs(self):
        for cl in range(1, 3):
            for rg in range(1, 3):
                self.noouttest(["add", "filesystem", "--type", "ext3",
                                "--cluster", "hacl%d" % cl,
                                "--resourcegroup", "hacl%dg%d" % (cl, rg),
                                "--filesystem", "hacl%dg%dfs" % (cl, rg),
                                "--mountpoint", "/d/d%d/app" % rg,
                                "--blockdevice", "/dev/vx/dsk/dg.0/gnr.%d" % rg,
                                "--bootmount", "--dumpfreq=1",
                                "--fsckpass=3", "--options=rw"])
                self.check_plenary_exists("resource",
                                          "cluster", "hacl%d" % cl,
                                          "resourcegroup", "hacl%dg%d" % (cl, rg),
                                          "filesystem", "hacl%dg%dfs" % (cl, rg),
                                          "config")

    def test_136_update_rg(self):
        command = ["update_resourcegroup", "--cluster", "hacl1",
                   "--resourcegroup", "hacl1g1",
                   "--required_type", "application"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Resource Group hacl1g1 already has a resource "
                         "of type filesystem.", command)

    def test_137_add_appsrv(self):
        # grep-friendly syntax
        ips = [self.net["unknown0"].usable[28],
               self.net["unknown0"].usable[29]]

        # Different location, different default DNS domains
        self.dsdb_expect_add("hacl1g1.aqd-unittest.ms.com", ips[0])
        self.dsdb_expect_add("hacl2g1.new-york.ms.com", ips[1])

        for cl in range(1, 3):
            self.statustest(["add", "service", "address",
                             "--cluster", "hacl%d" % cl,
                             "--resourcegroup", "hacl%dg1" % cl,
                             "--shortname", "hacl%dg1" % cl,
                             "--name", "hacl%dg1addr" % cl,
                             "--ip", ips[cl - 1]])
            self.check_plenary_exists("resource",
                                      "cluster", "hacl%d" % cl,
                                      "resourcegroup", "hacl%dg1" % cl,
                                      "service_address", "hacl%dg1addr" % cl,
                                      "config")
        self.dsdb_verify()

    def test_140_add_lb(self):
        # Multi-A record pointing to two different service IPs
        ips = [self.net["unknown0"].usable[30],
               self.net["unknown0"].usable[31]]
        # TODO: range(1, 3) once multi-A records are sorted out
        for cl in range(1, 2):
            self.dsdb_expect_add("hashared.aqd-unittest.ms.com", ips[cl - 1])
            self.statustest(["add", "service", "address",
                             "--cluster", "hacl%d" % cl,
                             "--resourcegroup", "hacl%dg2" % cl,
                             "--service_address", "hashared.aqd-unittest.ms.com",
                             "--name", "hacl%dg2addr" % cl,
                             "--ip", ips[cl - 1]])
            self.check_plenary_exists("resource",
                                      "cluster", "hacl%d" % cl,
                                      "resourcegroup", "hacl%dg2" % cl,
                                      "service_address", "hacl%dg2addr" % cl,
                                      "config")
        self.dsdb_verify()

    def test_145_check_hashared(self):
        ips = [self.net["unknown0"].usable[30],
               self.net["unknown0"].usable[31]]
        command = ["show", "fqdn", "--fqdn", "hashared.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "IP: %s" % ips[0], command)
        # self.matchoutput(out, "IP: %s" % ips[1], command)

    def test_150_make_cluster(self):
        self.statustest(["make", "cluster", "--cluster", "hacl1"])
        self.statustest(["make", "cluster", "--cluster", "hacl2"])

    def test_155_cat_hacl2(self):
        command = ["cat", "--cluster", "hacl2", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/cluster/max_hosts" = 2;', command)

    def test_155_cat_hacl1_client(self):
        command = ["cat", "--cluster", "hacl1", "--client"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/cluster/name" = "hacl1";', command)
        self.searchoutput(out,
                          r'include { if_exists\("features/" \+ value\("/system/archetype/name"\) \+ "/hacluster/hapersonality/config"\) };',
                          command)
        self.searchoutput(out,
                          r'"/system/cluster/resources/resourcegroup" = append\(create\("resource/cluster/hacl1/resourcegroup/hacl1g1/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"/system/cluster/resources/resourcegroup" = append\(create\("resource/cluster/hacl1/resourcegroup/hacl1g2/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"/system/cluster/resources/service_address" = append\(create\("resource/cluster/hacl1/service_address/hacl1/config"\)\);',
                          command)

    def test_161_add_allowed_personality(self):
        self.noouttest(["add_allowed_personality", "--archetype", "hacluster",
                        "--personality", "hapersonality", "--metacluster", "hamc1"])

    def test_162_add_clusters(self):
        self.noouttest(["update_cluster", "--cluster", "hacl1",
                        "--metacluster", "hamc1"])
        self.noouttest(["update_cluster", "--cluster", "hacl2",
                        "--metacluster", "hamc1"])

    def test_163_add_wrong_cluster(self):
        command = ["update_cluster", "--cluster", "utecl3",
                   "--metacluster", "hamc1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Personality esx_cluster/vulcan-10g-server-prod is "
                         "not allowed by the metacluster.  Allowed "
                         "personalities are: hacluster/hapersonality",
                         command)

    def test_164_show_hamc1(self):
        command = ["show_metacluster", "--metacluster", "hamc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Member: High Availability Cluster hacl1", command)
        self.matchoutput(out, "Member: High Availability Cluster hacl2", command)
        self.matchoutput(out,
                         "Allowed Personality: hapersonality Archetype: hacluster",
                         command)
        self.matchoutput(out, "Organization: ms", command)

    def test_165_fix_hamc1_location(self):
        self.noouttest(["update_metacluster", "--metacluster", "hamc1",
                        "--fix_location"])

    def test_166_verify_location(self):
        command = ["show_metacluster", "--metacluster", "hamc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Campus: ny", command)

    # TODO: there are no templates yet, so this does not work
    # def test_167_make_hamc1(self):
    #     self.statustest(["make_cluster", "--cluster", "hamc1"])

    def test_170_group_hacl1(self):
        command = ["update_cluster", "--cluster", "hacl1",
                   "--group_with", "hacl2"]
        self.noouttest(command)

    def test_171_verify_group(self):
        command = ["show_cluster", "--cluster", "hacl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Grouped with High Availability Cluster: hacl2", command)

        command = ["show_cluster", "--cluster", "hacl2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Grouped with High Availability Cluster: hacl1", command)

    def test_172_verify_search(self):
        command = ["search_cluster", "--grouped_with", "hacl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "hacl2", command)
        self.matchclean(out, "hacl1", command)

    def test_172_group_mismatch(self):
        command = ["update_cluster", "--cluster", "hacl2",
                   "--group_with", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "High Availability Cluster hacl2 and ESX "
                         "cluster utecl1 are already members of different "
                         "cluster groups.", command)

    def test_173_clear_group(self):
        command = ["update_cluster", "--cluster", "hacl1", "--clear_group"]
        self.noouttest(command)

    def test_174_verify_ungroup(self):
        command = ["show_cluster", "--cluster", "hacl1"]
        out = self.commandtest(command)
        self.matchclean(out, "Grouped", command)

        command = ["show_cluster", "--cluster", "hacl2"]
        out = self.commandtest(command)
        self.matchclean(out, "Grouped", command)

    def test_200_try_deco_hacl1(self):
        command = ["change_status", "--cluster", "hacl1", "--buildstatus",
                   "decommissioned"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cascaded decommissioning is not enabled for "
                         "archetype hacluster, please remove all members "
                         "first.",
                         command)

    def test_200_try_del_hacl1g1(self):
        command = ["del", "resourcegroup", "--cluster", "hacl1",
                   "--resourcegroup", "hacl1g1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Resource Group hacl1g1 contains service address "
                         "hacl1g1addr, please delete it first.",
                         command)

    def test_300_del_appsrv(self):
        ips = [self.net["unknown0"].usable[28],
               self.net["unknown0"].usable[29]]
        for cl in range(1, 3):
            self.dsdb_expect_delete(ips[cl - 1])
            self.noouttest(["del", "service", "address",
                            "--cluster", "hacl%d" % cl,
                            "--resourcegroup", "hacl%dg1" % cl,
                            "--name", "hacl%dg1addr" % cl])
            self.check_plenary_gone("resource", "cluster", "hacl%d" % cl,
                                    "resourcegroup", "hacl%dg1" % cl,
                                    "service_address", "hacl%dg1daddr" % cl,
                                    "config")
        self.dsdb_verify()

    def test_310_del_hacl1g1(self):
        plenarydir = self.config.get("broker", "plenarydir")
        cluster_res_dir = os.path.join(plenarydir, "resource", "cluster", "hacl1")
        rg_dir = os.path.join(cluster_res_dir, "resourcegroup", "hacl1g1")
        res_plenaries = [["resource", "cluster", "hacl1",
                          "resourcegroup", "hacl1g1", "config"],
                         ["resource", "cluster", "hacl1",
                          "resourcegroup", "hacl1g1",
                          "application", "hacl1g1app", "config"],
                         ["resource", "cluster", "hacl1",
                          "resourcegroup", "hacl1g1",
                          "filesystem", "hacl1g1fs", "config"]]

        # Verify that we got the paths right
        for path in res_plenaries:
            self.check_plenary_exists(*path)

        self.noouttest(["del", "resourcegroup", "--resourcegroup", "hacl1g1",
                        "--cluster", "hacl1"])

        # The resource plenaries should be gone
        for path in res_plenaries:
            self.check_plenary_gone(*path, directory_gone=True)

        # The directory should be gone as well
        self.assertFalse(os.path.exists(rg_dir),
                         "Plenary directory '%s' still exists" % rg_dir)

    def test_310_del_hacl2g1(self):
        self.noouttest(["del", "resourcegroup", "--resourcegroup", "hacl2g1",
                        "--cluster", "hacl2"])

    def test_320_del_hashared(self):
        ips = [self.net["unknown0"].usable[30],
               self.net["unknown0"].usable[31]]
        self.dsdb_expect_delete(ips[0])
        self.noouttest(["del", "service", "address", "--cluster", "hacl1",
                        "--resourcegroup", "hacl1g2",
                        "--name", "hacl1g2addr"])

        # command = ["search", "dns", "--fqdn", "hashared.aqd-unittest.ms.com",
        #            "--fullinfo"]
        # out = self.commandtest(command)
        # self.matchoutput(out, str(ips[1]), command)
        # self.matchclean(out, str(ips[0]), command)

        # self.dsdb_expect_delete(ips[1])
        # self.noouttest(["del", "service", "address", "--cluster", "hacl2",
        #                 "--resourcegroup", "hacl2g2",
        #                 "--name", "hacl2g2addr"])

        command = ["search", "dns", "--fqdn", "hashared.aqd-unittest.ms.com"]
        self.notfoundtest(command)

        self.dsdb_verify()

    def test_330_hacl1g2(self):
        self.noouttest(["del", "resourcegroup", "--resourcegroup", "hacl1g2",
                        "--cluster", "hacl1"])

    def test_330_hacl2g2(self):
        self.noouttest(["del", "resourcegroup", "--resourcegroup", "hacl2g2",
                        "--cluster", "hacl2"])

    def test_340_uncluster_firsthost(self):
        self.statustest(["uncluster", "--cluster", "hacl1",
                         "--hostname", "server2.aqd-unittest.ms.com"])
        self.statustest(["uncluster", "--cluster", "hacl2",
                         "--hostname", "server3.aqd-unittest.ms.com"])

    def test_350_uncluster_second(self):
        self.statustest(["uncluster", "--cluster", "hacl1",
                         "--hostname", "server4.aqd-unittest.ms.com"])
        self.statustest(["uncluster", "--cluster", "hacl2",
                         "--hostname", "server5.aqd-unittest.ms.com"])

    def test_355_del_cluster(self):
        command = ["del", "cluster", "--cluster", "hacl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "High Availability Cluster hacl1 still has service "
                         "address hacl1 assigned, please delete it first.",
                         command)

    def test_360_del_clustersrv(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[26])
        self.dsdb_expect_delete(self.net["unknown0"].usable[27])
        self.noouttest(["del", "service", "address", "--cluster", "hacl1",
                        "--name", "hacl1"])
        self.noouttest(["del", "service", "address", "--cluster", "hacl2",
                        "--name", "hacl2"])
        self.dsdb_verify()

    def test_370_del_clusters(self):
        self.statustest(["del", "cluster", "--cluster", "hacl1"])
        self.statustest(["del", "cluster", "--cluster", "hacl2"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUsecaseHACluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
