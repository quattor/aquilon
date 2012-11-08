#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the add resourcegroup command."""

import unittest
import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddResourceGroup(TestBrokerCommand):

    def test_100_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1"]
        self.successtest(command)

        command = ["show_resourcegroup", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utvcs1as1", command)
        self.matchoutput(out,
                         "Bound to: High Availability Cluster utvcs1",
                         command)

        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utvcs1as1", command)

    def test_101_add_rg_to_cluster_fail(self):
        command = ["add_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1", "--required_type=non-existent-type"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: non-existent-type is not a valid "
                         "resource type", command)

        command = ["add_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1", "--required_type=resourcegroup"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: A resourcegroup can't hold other "
                         "resourcegroups.", command)

    def test_110_add_fs_to_rg(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--resourcegroup=utvcs1as1", "--cluster=utvcs1"]
        self.successtest(command)

        command = ["show_filesystem", "--filesystem=fs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)
        self.matchoutput(out, "Bound to: Resource Group utvcs1as1", command)
        self.matchoutput(out, "Block Device: /dev/foo/bar", command)
        self.matchoutput(out, "Mount at boot: True", command)
        self.matchoutput(out, "Mountopts: ro", command)
        self.matchoutput(out, "Mountpoint: /mnt", command)
        self.matchoutput(out, "Dump Freq: 1", command)
        self.matchoutput(out, "Fsck Pass: 3", command)
        self.matchoutput(out, "Comments: testing", command)

    def test_200_show_rg(self):
        command = ["show", "resourcegroup", "--resourcegroup", "utvcs1as1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)

    def test_210_cat_cluster(self):
        command = ["cat", "--cluster", "utvcs1", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"/system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utvcs1/resourcegroup/utvcs1as1/config"));',
                         command)

    def test_210_cat_rg(self):
        command = ["cat", "--resourcegroup", "utvcs1as1", "--cluster", "utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"resources/filesystem" = '
                         'append(create("resource/cluster/utvcs1/resourcegroup/utvcs1as1/filesystem/fs1/config"));',
                         command)

    def test_210_cat_rg_generate(self):
        command = ["cat", "--resourcegroup", "utvcs1as1", "--cluster", "utvcs1",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"resources/filesystem" = '
                         'append(create("resource/cluster/utvcs1/resourcegroup/utvcs1as1/filesystem/fs1/config"));',
                         command)

    def test_210_cat_fs(self):
        command = ["cat", "--cluster", "utvcs1", "--resourcegroup", "utvcs1as1",
                   "--filesystem", "fs1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template resource/cluster/utvcs1/resourcegroup/utvcs1as1/filesystem/fs1/config;",
                         command)
        self.matchoutput(out, '"block_device_path" = "/dev/foo/bar";', command)

    def test_300_del_resourcegroup(self):
        # Check that the plenaries of contained resources get cleaned up
        plenarydir = self.config.get("broker", "plenarydir")
        fs_plenary = os.path.join(plenarydir, "resource", "cluster", "utvcs1",
                                  "resourcegroup", "utvcs1as1",
                                  "filesystem", "fs1", "config.tpl")
        rg_dir = os.path.join(plenarydir, "resource", "cluster", "utvcs1",
                              "resourcegroup", "utvcs1as1")
        rg_plenary = os.path.join(rg_dir, "config.tpl")

        # Verify that we got the paths right
        self.failUnless(os.path.exists(fs_plenary),
                        "Plenary '%s' does not exist" % fs_plenary)
        self.failUnless(os.path.exists(rg_plenary),
                        "Plenary '%s' does not exist" % rg_plenary)

        command = ["del_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1"]
        self.successtest(command)

        # The resource plenaries should be gone
        self.failIf(os.path.exists(fs_plenary),
                    "Plenary '%s' still exists" % fs_plenary)
        self.failIf(os.path.exists(rg_plenary),
                    "Plenary '%s' still exists" % rg_plenary)

        # The directory should be gone
        self.failIf(os.path.exists(rg_dir),
                    "Plenary directory '%s' still exists" % rg_dir)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddResourceGroup)
    unittest.TextTestRunner(verbosity=2).run(suite)
