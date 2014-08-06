#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing how a logical DB might be configured."""

import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUsecaseDatabase(TestBrokerCommand):

    def test_100_standalone_single_dbserver(self):
        command = ["add_filesystem", "--filesystem=gnr.0", "--type=ext3",
                   "--mountpoint=/d/d1/utdb1",
                   "--blockdevice=/dev/vx/dsk/dg.0/gnr.0",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_101_add_app(self):
        command = ["add_application", "--application=nydb1", "--eonid=42",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_105_reconfigure(self):
        command = ["reconfigure", "--personality=sybase-test",
                   "--buildstatus=rebuild",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_110_verify_show(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Application: nydb1", command)
        self.matchoutput(out, "Filesystem: gnr.0", command)

    def test_110_verify_cat(self):
        command = ["cat", "--hostname=server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/filesystem" = append(create("resource/host/server1.aqd-unittest.ms.com/filesystem/gnr.0/config"))', command)
        self.matchoutput(out, '"system/resources/application" = append(create("resource/host/server1.aqd-unittest.ms.com/application/nydb1/config"))', command)

    def test_120_standalone_two_dbserver(self):
        command = ["add_filesystem", "--filesystem=gnr.1", "--type=ext3",
                   "--mountpoint=/d/d1/utdb2",
                   "--blockdevice=/dev/vx/dsk/dg.0/gnr.1",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_111_add_app(self):
        command = ["add_application", "--application=utdb2", "--eonid=42",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_115_compile(self):
        command = ["compile", "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_130_verify_show(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Application: nydb1", command)
        self.matchoutput(out, "Filesystem: gnr.0", command)
        self.matchoutput(out, "Application: utdb2", command)
        self.matchoutput(out, "Filesystem: gnr.1", command)

    def test_130_verify_cat(self):
        command = ["cat", "--hostname=server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/filesystem" = append(create("resource/host/server1.aqd-unittest.ms.com/filesystem/gnr.0/config"))', command)
        self.matchoutput(out, '"system/resources/application" = append(create("resource/host/server1.aqd-unittest.ms.com/application/nydb1/config"))', command)
        self.matchoutput(out, '"system/resources/filesystem" = append(create("resource/host/server1.aqd-unittest.ms.com/filesystem/gnr.1/config"))', command)
        self.matchoutput(out, '"system/resources/application" = append(create("resource/host/server1.aqd-unittest.ms.com/application/utdb2/config"))', command)

    def test_190_del_fs1(self):
        command = ["del_filesystem", "--filesystem=gnr.0",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_190_del_app1(self):
        command = ["del_application", "--application=nydb1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_190_del_fs2(self):
        command = ["del_filesystem", "--filesystem=gnr.1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_190_del_app2(self):
        command = ["del_application", "--application=utdb2",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_200_clustered_dbserver(self):
        # We'll just do a single-node cluster for now
        command = ["add_cluster", "--cluster=nydb1",
                   "--campus=ny",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=vcs-msvcs"]
        self.successtest(command)

    def test_201_add_member(self):
        command = ["cluster", "--cluster=nydb1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_205_add_fs(self):
        command = ["add_filesystem", "--filesystem=gnr.0", "--type=ext3",
                   "--mountpoint=/d/d1/nydb1",
                   "--blockdevice=/dev/vx/dsk/dg.0/gnr.0",
                   "--nobootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--cluster=nydb1"]
        self.successtest(command)

    def test_205_add_app(self):
        command = ["add_application", "--application=nydb1", "--eonid=42",
                   "--cluster=nydb1"]
        self.successtest(command)

    def test_205_add_srv(self):
        ip = self.net["unknown0"].usable[25]
        self.dsdb_expect_add('nydb1nydb1.aqd-unittest.ms.com', ip)
        command = ["add_service_address", "--ip", ip, "--name", "nydb1nydb1",
                   "--service_address", "nydb1nydb1.aqd-unittest.ms.com",
                   "--cluster", "nydb1", "--interfaces", "eth0"]
        self.successtest(command)
        self.dsdb_verify()

    def test_210_compile(self):
        command = ["compile", "--cluster=nydb1"]
        self.successtest(command)

    def test_220_verify_show(self):
        srv_ip = self.net["unknown0"].usable[25]
        command = ["show_cluster", "--cluster=nydb1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Application: nydb1", command)
        self.matchoutput(out, "Filesystem: gnr.0", command)
        self.matchoutput(out, "Member: server1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Service Address: nydb1nydb1", command)
        self.matchoutput(out, "Address: nydb1nydb1.aqd-unittest.ms.com [%s]" %
                         srv_ip, command)
        self.matchoutput(out, "Interfaces: eth0", command)

    def test_220_verify_cat(self):
        command = ["cat", "--cluster=nydb1", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/filesystem" = append(create("resource/cluster/nydb1/filesystem/gnr.0/config"))', command)
        self.matchoutput(out, '"system/resources/application" = append(create("resource/cluster/nydb1/application/nydb1/config"))', command)
        self.matchoutput(out,
                         '"system/resources/service_address" = '
                         'append(create("resource/cluster/nydb1/service_address/nydb1nydb1/config"))',
                         command)

    def test_290_cleanup_cluster(self):
        # Check that the plenaries of contained resources get cleaned up
        plenarydir = self.config.get("broker", "plenarydir")
        cluster_dir = os.path.join(plenarydir, "cluster", "nydb1")
        cluster_res_dir = os.path.join(plenarydir, "resource", "cluster", "nydb1")
        res_plenaries = [["resource", "cluster", "nydb1",
                          "filesystem", "gnr.0", "config"],
                         ["resource", "cluster", "nydb1",
                          "application", "nydb1", "config"],
                         ["resource", "cluster", "nydb1",
                          "service_address", "nydb1nydb1", "config"]]

        # Verify that we got the paths right
        for path in res_plenaries:
            self.check_plenary_exists(*path)

        self.dsdb_expect_delete(self.net["unknown0"].usable[25])
        command = ["del_service_address", "--cluster=nydb1",
                   "--name", "nydb1nydb1"]
        self.successtest(command)
        self.dsdb_verify()

        command = ["uncluster", "--hostname=server1.aqd-unittest.ms.com",
                   "--cluster=nydb1"]
        self.successtest(command)
        command = ["del_cluster", "--cluster=nydb1"]
        self.successtest(command)

        # The resource plenaries should be gone
        for path in res_plenaries:
            self.check_plenary_gone(*path, directory_gone=True)

        # The directories should be gone as well
        self.failIf(os.path.exists(cluster_res_dir),
                    "Plenary directory '%s' still exists" % cluster_res_dir)
        self.failIf(os.path.exists(cluster_dir),
                    "Plenary directory '%s' still exists" % cluster_dir)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUsecaseDatabase)
    unittest.TextTestRunner(verbosity=2).run(suite)
