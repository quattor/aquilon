#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011-2019  Contributor
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
"""Module for testing the add resourcegroup command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddResourceGroup(TestBrokerCommand):

    def test_000_early_constraints(self):
        # Test what happens if the holder never had any resources
        command = ["show_filesystem", "--cluster=utvcs1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                     "High Availability Cluster utvcs1 has no resources.",
                     command)
        command = ["search_filesystem", "--cluster=utvcs1"]
        self.noouttest(command)

    def test_100_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1",
                   "--comment", "Some resourcegroup comments"]
        self.successtest(command)

    def test_105_show_resourcegroup(self):
        command = ["show_resourcegroup", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utvcs1as1", command)
        self.matchoutput(out,
                         "Bound to: High Availability Cluster utvcs1",
                         command)
        self.matchoutput(out, "Comments: Some resourcegroup comments", command)
        self.matchclean(out, "Type:", command)

    def test_110_add_fs_to_rg(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/vx/dsk/dg.0/gnr.0",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--resourcegroup=utvcs1as1", "--cluster=utvcs1"]
        self.successtest(command)

    def test_115_show_filesystem(self):
        command = ["show_filesystem", "--filesystem=fs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)
        self.matchoutput(out, "Bound to: Resource Group utvcs1as1", command)
        self.matchoutput(out, "Block Device: /dev/vx/dsk/dg.0/gnr.0", command)
        self.matchoutput(out, "Mount at boot: True", command)
        self.matchoutput(out, "Mountopts: ro", command)
        self.matchoutput(out, "Mountpoint: /mnt", command)
        self.matchoutput(out, "Dump Freq: 1", command)
        self.matchoutput(out, "Fsck Pass: 3", command)
        self.matchoutput(out, "Transport Type: None", command)
        self.matchoutput(out, "Transport ID: None", command)

    def test_115_show_resourcegroup(self):
        command = ["show", "resourcegroup", "--resourcegroup", "utvcs1as1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)

    def test_115_cat_cluster(self):
        command = ["cat", "--cluster", "utvcs1", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utvcs1/resourcegroup/utvcs1as1/config"));',
                         command)

    def test_115_cat_resourcegroup(self):
        command = ["cat", "--resourcegroup", "utvcs1as1", "--cluster", "utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"resources/filesystem" = '
                         'append(create("resource/cluster/utvcs1/resourcegroup/utvcs1as1/filesystem/fs1/config"));',
                         command)

    def test_115_cat_resourcegroup_generate(self):
        command = ["cat", "--resourcegroup", "utvcs1as1", "--cluster", "utvcs1",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"resources/filesystem" = '
                         'append(create("resource/cluster/utvcs1/resourcegroup/utvcs1as1/filesystem/fs1/config"));',
                         command)

    def test_115_cat_filesystem(self):
        command = ["cat", "--cluster", "utvcs1", "--resourcegroup", "utvcs1as1",
                   "--filesystem", "fs1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template resource/cluster/utvcs1/resourcegroup/utvcs1as1/filesystem/fs1/config;",
                         command)
        self.matchoutput(out, '"block_device_path" = "/dev/vx/dsk/dg.0/gnr.0";', command)

    def test_115_show_cluster(self):
        command = ["show", "cluster", "--cluster", "utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "    Resource Group: utvcs1", command)
        self.matchoutput(out, "      Filesystem: fs1", command)

    def test_115_show_cluster_proto(self):
        command = ["show", "cluster", "--cluster", "utvcs1", "--format", "proto"]
        cluster = self.protobuftest(command, expect=1)[0]
        rg_msg = None
        for resource in cluster.resources:
            if resource.name == "utvcs1as1" and \
               resource.type == "resourcegroup":
                rg_msg = resource
        self.assertTrue(rg_msg,
                        "Resourcegroup utvcs1as1 not found in the resources. "
                        "Existing resources: %s" %
                        ", ".join("%s %s" % (res.type, res.name)
                                  for res in cluster.resources))
        fs_found = False
        for resource in rg_msg.resourcegroup.resources:
            if resource.name == "fs1" and resource.type == "filesystem":
                fs_found = True
                self.assertEqual(resource.fsdata.fstype, "ext3")
                self.assertEqual(resource.fsdata.mountpoint, "/mnt")
                self.assertEqual(resource.fsdata.mount, True)
                self.assertEqual(resource.fsdata.blockdevice, "/dev/vx/dsk/dg.0/gnr.0")
                self.assertEqual(resource.fsdata.opts, "ro")
                self.assertEqual(resource.fsdata.freq, 1)
                self.assertEqual(resource.fsdata.passno, 3)
        self.assertTrue(fs_found,
                        "Filesystem fs1 not found in the resourcegroup. "
                        "Existing resources: %s" %
                        ", ".join("%s %s" % (res.type, res.name)
                                  for res in rg_msg.resourcegroup.resources))

    def test_120_update_rg(self):
        self.noouttest(["update_resourcegroup", "--cluster", "utvcs1",
                        "--resourcegroup", "utvcs1as1",
                        "--comments", "New resourcegroup comments",
                        "--required_type", "FiLeSyStEm"])

    def test_125_verify_update(self):
        command = ["show_resourcegroup", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utvcs1as1", command)
        self.matchoutput(out,
                         "Bound to: High Availability Cluster utvcs1",
                         command)
        self.matchoutput(out, "Comments: New resourcegroup comments", command)
        self.matchoutput(out, "Type: filesystem", command)

    def test_126_type_mismatch(self):
        command = ["add_application", "--cluster", "utvcs1",
                   "--resourcegroup", "utvcs1as1",
                   "--application", "testapp", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Resource Group utvcs1as1 may contain resources "
                         "of type filesystem only.", command)

    def test_130_reset_data(self):
        self.noouttest(["update_resourcegroup", "--cluster", "utvcs1",
                        "--resourcegroup", "utvcs1as1",
                        "--comments", "", "--required_type", ""])

    def test_135_verify_reset(self):
        command = ["show_resourcegroup", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utvcs1as1", command)
        self.matchoutput(out,
                         "Bound to: High Availability Cluster utvcs1",
                         command)
        self.matchclean(out, "Comments:", command)
        self.searchclean(out, r"^\s*Type:", command)

    def test_140_add_empty(self):
        # Add an empty resourcegroup, that won't have any resources in it
        command = ["add_resourcegroup", "--resourcegroup", "empty",
                   "--cluster", "utvcs1"]
        self.successtest(command)

    def test_141_update_empty(self):
        # Test updating a resourcegroup that never had any resources, so the
        # BundleResource object is never created
        command = ["update_resourcegroup", "--resourcegroup", "empty",
                   "--cluster", "utvcs1", "--required_type", "filesystem"]
        self.successtest(command)

    def test_142_del_empty(self):
        # Test deleting a resourcegroup that never had any resources, so the
        # BundleResource object is never created
        command = ["del_resourcegroup", "--resourcegroup", "empty",
                   "--cluster", "utvcs1"]
        self.successtest(command)

    def test_150_add_utmc8_rg(self):
        command = ["add_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--required_type=share"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Please use the --metacluster option for metaclusters.",
                         command)

        command = ["add_resourcegroup", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8", "--required_type=share"]
        self.noouttest(command)

    def test_155_show_utmc8_rg(self):
        command = ["show_resourcegroup", "--metacluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Bound to: ESX Metacluster utmc8", command)

    def test_160_add_utmc9_rg(self):
        self.statustest(["add_resourcegroup", "--resourcegroup", "utrg2",
                         "--hostname", "evh83.aqd-unittest.ms.com"])

    def test_200_add_bad_type(self):
        command = ["add_resourcegroup", "--resourcegroup=utvcs1as2",
                   "--cluster=utvcs1", "--required_type=no-such-resource-type"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Unknown resource type 'no-such-resource-type'.",
                         command)

    def test_200_stacked_resourcegroup(self):
        command = ["add_resourcegroup", "--resourcegroup=utvcs1as2",
                   "--cluster=utvcs1", "--required_type=resourcegroup"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: A resourcegroup can't hold other "
                         "resourcegroups.", command)

    def test_300_show_all(self):
        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utvcs1", command)
        self.matchoutput(out, "Resource Group: utvcs1as1", command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Resource Group: utmc8as2", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddResourceGroup)
    unittest.TextTestRunner(verbosity=2).run(suite)
