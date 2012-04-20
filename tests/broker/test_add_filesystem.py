#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
        self.matchoutput(out, '"/system/resources/filesystem" = push(create("resource/host/server1.aqd-unittest.ms.com/filesystem/fs1/config"))', command)
        self.matchoutput(out, '"/system/resources/filesystem" = push(create("resource/host/server1.aqd-unittest.ms.com/filesystem/fs2/config"))', command)

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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddFilesystem)
    unittest.TextTestRunner(verbosity=2).run(suite)

