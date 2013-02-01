#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing how a HA cluster might be configured."""

import unittest
import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUsecaseHACluster(TestBrokerCommand):

    def test_100_add_cluster1(self):
        user = self.config.get("unittest", "user")
        command = ["add", "cluster", "--cluster", "hacl1", "--campus", "ny",
                   "--down_hosts_threshold", 0, "--archetype", "hacluster",
                   "--sandbox", "%s/utsandbox" % user,
                   "--personality", "vcs-msvcs"]
        self.successtest(command)

    def test_100_add_cluster2(self):
        user = self.config.get("unittest", "user")
        command = ["add", "cluster", "--cluster", "hacl2", "--campus", "ny",
                   "--down_hosts_threshold", 0, "--archetype", "hacluster",
                   "--sandbox", "%s/utsandbox" % user,
                   "--personality", "vcs-msvcs"]
        self.successtest(command)

    def test_110_add_members(self):
        for i in range(0, 4):
            server_idx = i + 2
            cluster_idx = (i % 2) + 1
            self.successtest(["cluster", "--cluster", "hacl%d" % cluster_idx,
                              "--hostname", "server%d.aqd-unittest.ms.com" %
                              server_idx])

    def test_115_add_cluster_srv(self):
        ip1 = self.net.unknown[0].usable[26]
        ip2 = self.net.unknown[0].usable[27]
        self.dsdb_expect_add("hacl1.aqd-unittest.ms.com", ip1)
        self.successtest(["add", "service", "address",
                          "--service_address", "hacl1.aqd-unittest.ms.com",
                          "--name", "hacl1", "--cluster", "hacl1",
                          "--ip", ip1, "--interfaces", "eth0"])
        self.dsdb_expect_add("hacl2.aqd-unittest.ms.com", ip2)
        self.successtest(["add", "service", "address",
                          "--service_address", "hacl2.aqd-unittest.ms.com",
                          "--name", "hacl2", "--cluster", "hacl2",
                          "--ip", ip2, "--interfaces", "eth0"])
        self.dsdb_verify()

    def test_120_add_resourcegroups(self):
        plenarydir = self.config.get("broker", "plenarydir")
        for cl in range(1, 3):
            cluster_res_dir = os.path.join(plenarydir, "resource", "cluster",
                                           "hacl%d" % cl)
            for rg in range(1, 3):
                rg_dir = os.path.join(cluster_res_dir, "resourcegroup",
                                      "hacl%dg%d" % (cl, rg))
                plenary = os.path.join(rg_dir, "config.tpl")

                self.successtest(["add", "resourcegroup",
                                  "--cluster", "hacl%d" % cl,
                                  "--resourcegroup", "hacl%dg%d" % (cl, rg)])
                self.failUnless(os.path.exists(plenary),
                                "Plenary '%s' does not exist" % plenary)

    def test_125_add_apps(self):
        plenarydir = self.config.get("broker", "plenarydir")
        for cl in range(1, 3):
            cluster_res_dir = os.path.join(plenarydir, "resource", "cluster",
                                           "hacl%d" % cl)
            for rg in range(1, 3):
                rg_dir = os.path.join(cluster_res_dir, "resourcegroup",
                                      "hacl%dg%d" % (cl, rg))
                plenary = os.path.join(rg_dir, "application",
                                       "hacl%dg%dapp" % (cl, rg), "config.tpl")

                self.successtest(["add", "application",
                                  "--cluster", "hacl%d" % cl,
                                  "--resourcegroup", "hacl%dg%d" % (cl, rg),
                                  "--application", "hacl%dg%dapp" % (cl, rg),
                                  "--eonid", 42])
                self.failUnless(os.path.exists(plenary),
                                "Plenary '%s' does not exist" % plenary)

    def test_125_add_fs(self):
        plenarydir = self.config.get("broker", "plenarydir")
        for cl in range(1, 3):
            cluster_res_dir = os.path.join(plenarydir, "resource", "cluster",
                                           "hacl%d" % cl)
            for rg in range(1, 3):
                rg_dir = os.path.join(cluster_res_dir, "resourcegroup",
                                      "hacl%dg%d" % (cl, rg))
                plenary = os.path.join(rg_dir, "filesystem",
                                       "hacl%dg%dfs" % (cl, rg), "config.tpl")
                self.successtest(["add", "filesystem", "--type", "ext3",
                                  "--cluster", "hacl%d" % cl,
                                  "--resourcegroup", "hacl%dg%d" % (cl, rg),
                                  "--filesystem", "hacl%dg%dfs" % (cl, rg),
                                  "--mountpoint", "/d/d%d/app" % rg,
                                  "--blockdevice", "/dev/vx/dg.0/gnr.%d" % rg,
                                  "--bootmount", "--dumpfreq=1",
                                  "--fsckpass=3", "--options=rw"])
                self.failUnless(os.path.exists(plenary),
                                "Plenary '%s' does not exist" % plenary)

    def test_125_add_appsrv(self):
        # grep-friendly syntax
        ips = [self.net.unknown[0].usable[28],
               self.net.unknown[0].usable[29]]
        plenarydir = self.config.get("broker", "plenarydir")
        for cl in range(1, 3):
            cluster_res_dir = os.path.join(plenarydir, "resource", "cluster",
                                           "hacl%d" % cl)
            rg_dir = os.path.join(cluster_res_dir, "resourcegroup",
                                  "hacl%dg1" % cl)
            plenary = os.path.join(rg_dir, "service_address",
                                   "hacl%dg1addr" % cl, "config.tpl")

            self.dsdb_expect_add("hacl%dg1.aqd-unittest.ms.com" % cl,
                                 ips[cl - 1])
            self.successtest(["add", "service", "address",
                              "--cluster", "hacl%d" % cl,
                              "--resourcegroup", "hacl%dg1" % cl,
                              "--service_address", "hacl%dg1.aqd-unittest.ms.com" % cl,
                              "--name", "hacl%dg1addr" % cl,
                              "--ip", ips[cl - 1], "--interfaces", "eth0"])
            self.failUnless(os.path.exists(plenary),
                            "Plenary '%s' does not exist" % plenary)
        self.dsdb_verify()

    def test_130_add_lb(self):
        # Multi-A record pointing to two different service IPs
        ips = [self.net.unknown[0].usable[30],
               self.net.unknown[0].usable[31]]
        plenarydir = self.config.get("broker", "plenarydir")
        # TODO: range(1, 3) once multi-A records are sorted out
        for cl in range(1, 2):
            cluster_res_dir = os.path.join(plenarydir, "resource", "cluster",
                                           "hacl%d" % cl)
            rg_dir = os.path.join(cluster_res_dir, "resourcegroup",
                                  "hacl%dg2" % cl)
            plenary = os.path.join(rg_dir, "service_address",
                                   "hacl%dg2addr" % cl, "config.tpl")

            self.dsdb_expect_add("hashared.aqd-unittest.ms.com", ips[cl - 1])
            self.successtest(["add", "service", "address",
                              "--cluster", "hacl%d" % cl,
                              "--resourcegroup", "hacl%dg2" % cl,
                              "--service_address", "hashared.aqd-unittest.ms.com",
                              "--name", "hacl%dg2addr" % cl,
                              "--ip", ips[cl - 1], "--interfaces", "eth0"])
            self.failUnless(os.path.exists(plenary),
                            "Plenary '%s' does not exist" % plenary)
        self.dsdb_verify()

    def test_200_make_cluster(self):
        self.successtest(["make", "cluster", "--cluster", "hacl1"])
        self.successtest(["make", "cluster", "--cluster", "hacl2"])

    def test_300_check_dns(self):
        ips = [self.net.unknown[0].usable[30],
               self.net.unknown[0].usable[31]]
        command = ["show", "fqdn", "--fqdn", "hashared.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "IP: %s" % ips[0], command)
        #self.matchoutput(out, "IP: %s" % ips[1], command)

    def test_400_try_deco_hacl1(self):
        command = ["change_status", "--cluster", "hacl1", "--buildstatus",
                  "decommissioned"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot change state to decommissioned, as "
                         "High Availability Cluster hacl1's archetype "
                         "is hacluster.",
                         command)

    def test_900_try_del_hacl1g1(self):
        command = ["del", "resourcegroup", "--cluster", "hacl1",
                   "--resourcegroup", "hacl1g1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Resource Group hacl1g1 contains service address "
                         "hacl1g1addr, please delete it first.",
                         command)

    def test_910_del_appsrv(self):
        plenarydir = self.config.get("broker", "plenarydir")
        ips = [self.net.unknown[0].usable[28],
               self.net.unknown[0].usable[29]]
        for cl in range(1, 3):
            cluster_res_dir = os.path.join(plenarydir, "resource", "cluster",
                                           "hacl%d" % cl)
            rg_dir = os.path.join(cluster_res_dir, "resourcegroup",
                                  "hacl%dg1" % cl)
            plenary = os.path.join(rg_dir, "service_address",
                                   "hacl%dg1addr" % cl, "config.tpl")
            self.dsdb_expect_delete(ips[cl - 1])
            self.successtest(["del", "service", "address",
                              "--cluster", "hacl%d" % cl,
                              "--resourcegroup", "hacl%dg1" % cl,
                              "--name", "hacl%dg1addr" % cl])
            self.failIf(os.path.exists(plenary),
                        "Plenary '%s' still exists" % plenary)
        self.dsdb_verify()

    def test_920_del_hacl1g1(self):
        plenarydir = self.config.get("broker", "plenarydir")
        cluster_res_dir = os.path.join(plenarydir, "resource", "cluster", "hacl1")
        rg_dir = os.path.join(cluster_res_dir, "resourcegroup", "hacl1g1")
        res_plenaries = [os.path.join(rg_dir, "config.tpl"),
                         os.path.join(rg_dir, "application", "hacl1g1app",
                                      "config.tpl"),
                         os.path.join(rg_dir, "filesystem", "hacl1g1fs",
                                      "config.tpl")]

        # Verify that we got the paths right
        for plenary in res_plenaries:
            self.failUnless(os.path.exists(plenary),
                            "Plenary '%s' does not exist" % plenary)

        self.successtest(["del", "resourcegroup", "--resourcegroup", "hacl1g1",
                          "--cluster", "hacl1"])

        # The resource plenaries should be gone
        for plenary in res_plenaries:
            self.failIf(os.path.exists(plenary),
                        "Plenary '%s' still exists" % plenary)

        # The directory should be gone as well
        self.failIf(os.path.exists(rg_dir),
                    "Plenary directory '%s' still exists" % rg_dir)

    def test_920_del_hacl2g1(self):
        self.successtest(["del", "resourcegroup", "--resourcegroup", "hacl2g1",
                          "--cluster", "hacl2"])

    def test_930_del_hashared(self):
        ips = [self.net.unknown[0].usable[30],
               self.net.unknown[0].usable[31]]
        self.dsdb_expect_delete(ips[0])
        self.successtest(["del", "service", "address", "--cluster", "hacl1",
                          "--resourcegroup", "hacl1g2",
                          "--name", "hacl1g2addr"])

        #command = ["search", "dns", "--fqdn", "hashared.aqd-unittest.ms.com",
        #           "--fullinfo"]
        #out = self.commandtest(command)
        #self.matchoutput(out, str(ips[1]), command)
        #self.matchclean(out, str(ips[0]), command)

        #self.dsdb_expect_delete(ips[1])
        #self.successtest(["del", "service", "address", "--cluster", "hacl2",
        #                  "--resourcegroup", "hacl2g2",
        #                  "--name", "hacl2g2addr"])

        command = ["search", "dns", "--fqdn", "hashared.aqd-unittest.ms.com"]
        self.notfoundtest(command)

        self.dsdb_verify()

    def test_940_hacl1g2(self):
        self.successtest(["del", "resourcegroup", "--resourcegroup", "hacl1g2",
                          "--cluster", "hacl1"])

    def test_940_hacl2g2(self):
        self.successtest(["del", "resourcegroup", "--resourcegroup", "hacl2g2",
                          "--cluster", "hacl2"])

    def test_950_uncluster_firsthost(self):
        self.successtest(["uncluster", "--cluster", "hacl1",
                          "--hostname", "server2.aqd-unittest.ms.com"])
        self.successtest(["uncluster", "--cluster", "hacl2",
                          "--hostname", "server3.aqd-unittest.ms.com"])

    def test_955_uncluster_fail(self):
        command = ["uncluster", "--cluster", "hacl1",
                   "--hostname", "server4.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "High Availability Cluster hacl1 still has service "
                         "address hacl1 assigned, removing the last cluster "
                         "member is not allowed.",
                         command)

    def test_960_del_clustersrv(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[26])
        self.dsdb_expect_delete(self.net.unknown[0].usable[27])
        self.successtest(["del", "service", "address", "--cluster", "hacl1",
                          "--name", "hacl1"])
        self.successtest(["del", "service", "address", "--cluster", "hacl2",
                          "--name", "hacl2"])
        self.dsdb_verify()

    def test_970_uncluster_second(self):
        self.successtest(["uncluster", "--cluster", "hacl1",
                          "--hostname", "server4.aqd-unittest.ms.com"])
        self.successtest(["uncluster", "--cluster", "hacl2",
                          "--hostname", "server5.aqd-unittest.ms.com"])

    def test_980_del_clusters(self):
        self.successtest(["del", "cluster", "--cluster", "hacl1"])
        self.successtest(["del", "cluster", "--cluster", "hacl2"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUsecaseHACluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
