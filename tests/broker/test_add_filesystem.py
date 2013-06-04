#!/usr/bin/env python2.6
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
"""Module for testing the add filesystem command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddFilesystem(TestBrokerCommand):

    def test_00_basic_filesystem(self):
        command = ["show_filesystem", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host server1.aqd-unittest.ms.com has no resources.",
                         command)

        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_filesystem", "--filesystem=fs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Block Device: /dev/foo/bar", command)
        self.matchoutput(out, "Mount at boot: True", command)
        self.matchoutput(out, "Mountopts: ro", command)
        self.matchoutput(out, "Mountpoint: /mnt", command)
        self.matchoutput(out, "Dump Freq: 1", command)
        self.matchoutput(out, "Fsck Pass: 3", command)
        self.matchoutput(out, "Comments: testing", command)

        command = ["cat", "--filesystem=fs1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/host/server1.aqd-unittest.ms.com/filesystem/fs1/config;", command)
        self.matchoutput(out, '"type" = "ext3";', command)
        self.matchoutput(out, '"mountpoint" = "/mnt";', command)
        self.matchoutput(out, '"mount" = true;', command)
        self.matchoutput(out, '"block_device_path" = "/dev/foo/bar"',
                         command)
        self.matchoutput(out, '"mountopts" = "ro";', command)
        self.matchoutput(out, '"freq" = 1;', command)
        self.matchoutput(out, '"pass" = 3;', command)

        command = ["cat", "--filesystem=fs1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--generate"]
        newout = self.commandtest(command)
        self.assertEqual(out, newout)

        command = ["show_filesystem", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)

    def test_10_defaults(self):
        command = ["add_filesystem", "--filesystem=fs2", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount", "--host=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_filesystem", "--filesystem=fs2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs2", command)
        self.matchoutput(out, "Block Device: /dev/foo/bar", command)
        self.matchoutput(out, "Mount at boot: True", command)
        self.matchoutput(out, "Mountopts: None", command)
        self.matchoutput(out, "Mountpoint: /mnt", command)
        self.matchoutput(out, "Dump Freq: 0", command)
        self.matchoutput(out, "Fsck Pass: 2", command)
        self.matchclean(out, "Comments", command)

    def test_11_addexisting(self):
        command = ["add_filesystem", "--filesystem=fs2", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount", "--host=server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_15_notfoundfs(self):
        command = ["show_filesystem", "--filesystem=fs-does-not-exist"]
        self.notfoundtest(command)

        command = ["cat", "--filesystem=fs-does-not-exist",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_30_checkthehost(self):
        command = ["show_host", "--host=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)
        self.matchoutput(out, "Filesystem: fs2", command)

        command = ["make", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.successtest(command)

        command = ["cat", "--generate",
                   "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/filesystem" = append(create("resource/host/server1.aqd-unittest.ms.com/filesystem/fs1/config"))', command)
        self.matchoutput(out, '"system/resources/filesystem" = append(create("resource/host/server1.aqd-unittest.ms.com/filesystem/fs2/config"))', command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        for resource in host.resources:
            if resource.name == "fs1" and resource.type == "filesystem":
                self.assertEqual(resource.fsdata.mountpoint, "/mnt")

    def test_50_add_to_cluster(self):
        command = ["show_filesystem", "--cluster=utvcs1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "High Availability Cluster utvcs1 has no resources.",
                         command)

        command = ["add_filesystem", "--filesystem=fsshared", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--nobootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--comments=cluster testing",
                   "--cluster=utvcs1"]
        self.successtest(command)

        command = ["show_filesystem", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fsshared", command)
        self.matchoutput(out, "Bound to: High Availability Cluster utvcs1",
                         command)
        self.matchoutput(out, "Block Device: /dev/foo/bar", command)
        self.matchoutput(out, "Mount at boot: False", command)
        self.matchoutput(out, "Mountopts: rw", command)
        self.matchoutput(out, "Mountpoint: /mnt", command)
        self.matchoutput(out, "Dump Freq: 1", command)
        self.matchoutput(out, "Fsck Pass: 3", command)
        self.matchoutput(out, "Comments: cluster testing", command)

        command = ["show_filesystem", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fsshared", command)

    def test_60_show_all_proto(self):
        command = ["show", "filesystem", "--all", "--format", "proto"]
        out = self.commandtest(command)
        self.parse_resourcelist_msg(out, expect=3)

    def test_del_filesystem(self):
        command = ["del_filesystem", "--filesystem=fs2",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["del_filesystem", "--filesystem=fsshared",
                   "--cluster=utvcs1"]
        self.successtest(command)

        # fs1 is not deleted here, it will be removed when the host is deleted.

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddFilesystem)
    unittest.TextTestRunner(verbosity=2).run(suite)
