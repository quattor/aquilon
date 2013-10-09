#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the update disk command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUpdateDisk(TestBrokerCommand):

    def test_100_update_ut3c1n3_sda(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--size", "50", "--comments", "Other disk comments",
                   "--controller", "sata"]
        self.noouttest(command)

    def test_101_update_ut3c1n3_c0d0(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "c0d0",
                   "--rename_to", "c0d1", "--boot"]
        self.noouttest(command)

    def test_105_show_ut3c1n3(self):
        command = ["show_machine", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Disk: sda 50 GB sata \(local\)\s*'
                          r'Comments: Other disk comments',
                          command)
        self.searchoutput(out,
                          r"Disk: c0d1 34 GB cciss \(local\) \[boot\]$",
                          command)

    def test_105_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"harddisks/{cciss/c0d1}" = '
                          r'create\("hardware/harddisk/generic/cciss",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 34\*GB,\s*'
                          r'"interface", "cciss"\s*\);',
                          command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = '
                          r'create\("hardware/harddisk/generic/sata",\s*'
                          r'"capacity", 50\*GB,\s*'
                          r'"interface", "sata"\s*\);',
                          command)
        self.matchclean(out, "c0d0", command)

    def test_110_prepare_vm_test(self):
        self.noouttest(["add_filesystem", "--filesystem", "disk_update_test",
                        "--cluster", "utecl5", "--type", "ext3",
                        "--mountpoint", "/backend", "--blockdevice", "sdc",
                        "--bootmount"])

    def test_111_move_disk_to_fs(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--filesystem", "disk_update_test", "--address", "0:1",
                   "--snapshot"]
        self.noouttest(command)

    def test_112_verify_utecl5_share(self):
        command = ["search_machine", "--share", "utecl5_share"]
        out = self.commandtest(command)
        self.matchclean(out, "evm10", command)

    def test_112_verify_fs(self):
        command = ["show_filesystem", "--filesystem", "disk_update_test",
                   "--cluster", "utecl5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Virtual Disk Count: 1", command)

    def test_112_show_evm10(self):
        command = ["show", "machine", "--machine", "evm10"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Disk: sda 45 GB scsi (virtual_localdisk from "
                         "disk_update_test) [boot, snapshot]",
                         command)
        self.matchclean(out, "utecl5_share", command)

    def test_112_cat_evm10(self):
        command = ["cat", "--machine", "evm10"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = nlist\(\s*'
                          r'"address", "0:1",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 45\*GB,\s*'
                          r'"filesystemname", "disk_update_test",\s*'
                          r'"interface", "scsi",\s*'
                          r'"mountpoint", "/backend",\s*'
                          r'"path", "evm10/sda\.vmdk",\s*'
                          r'"snapshot", true\s*\);',
                          command)
        self.matchclean(out, "utecl5_share", command)

    def test_113_move_disk_to_share(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--share", "utecl5_share", "--address", "0:0",
                   "--nosnapshot"]
        self.noouttest(command)

    def test_114_verify_utecl5_share(self):
        command = ["search_machine", "--share", "utecl5_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm10", command)

    def test_114_verify_fs(self):
        command = ["show_filesystem", "--filesystem", "disk_update_test",
                   "--cluster", "utecl5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Virtual Disk Count: 0", command)

    def test_114_show_evm10(self):
        command = ["show", "machine", "--machine", "evm10"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Disk: sda 45 GB scsi (virtual_disk from "
                         "utecl5_share) [boot]",
                         command)
        self.matchclean(out, "disk_update_test", command)

    def test_114_cat_evm10(self):
        command = ["cat", "--machine", "evm10"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = nlist\(\s*'
                          r'"address", "0:0",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 45\*GB,\s*'
                          r'"interface", "scsi",\s*'
                          r'"mountpoint", "/vol/lnn30f1v1/utecl5_share",\s*'
                          r'"path", "evm10/sda.vmdk",\s*'
                          r'"server", "lnn30f1",\s*'
                          r'"sharename", "utecl5_share",\s*'
                          r'"snapshot", false\s*\);',
                          command)
        self.matchclean(out, "disk_update_test", command)

    def test_119_cleanup_vm_terst(self):
        self.noouttest(["del_filesystem", "--cluster", "utecl5",
                        "--filesystem", "disk_update_test"])

    def test_300_rename_exists(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--rename_to", "c0d1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "LocalDisk c0d1, machine "
                         "unittest00.one-nyp.ms.com already exists.", command)

    def test_300_bad_controller(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--controller", "bad-controller"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "bad-controller is not a valid controller type, "
                         "use one of: cciss, ide, sas, sata, scsi, flash, "
                         "fibrechannel.",
                         command)

    def test_300_bad_address(self):
        command = ["update_disk", "--machine", "evm10", "--disk", "sda",
                   "--address", "bad-address"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         r"Disk address 'bad-address' is not valid, it must "
                         r"match \d+:\d+ (e.g. 0:0).",
                         command)

    def test_300_address_localdisk(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--address", "0:0"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Bus address can only be set for virtual disks.",
                         command)

    def test_300_snapshot_localdisk(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--snapshot"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Snapshot capability can only be set for "
                         "virtual disks.", command)

    def test_300_share_localdisk(self):
        command = ["update_disk", "--machine", "ut3c1n3", "--disk", "sda",
                   "--share", "test_share_1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Disk sda of machine unittest00.one-nyp.ms.com "
                         "is not a virtual disk, changing the backend store is "
                         "not possible.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
