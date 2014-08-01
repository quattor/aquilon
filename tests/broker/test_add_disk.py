#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the add disk command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddDisk(TestBrokerCommand):

    def test_100_add_ut3c5n10_disk(self):
        self.noouttest(["add", "disk", "--machine", "ut3c5n10",
                        "--disk", "sdb", "--controller", "scsi",
                        "--address", "0:0:1:0",
                        "--size", "34", "--comments", "Disk comments"])

    def test_110_add_ut3c1n3_disk(self):
        command = ["add", "disk", "--machine", "ut3c1n3", "--disk", "c0d0",
                   "--controller", "cciss", "--size", "34",
                   "--wwn", "600508b112233445566778899aabbccd",
                   "--bus_address", "pci:0000:01:00.0"]
        self.noouttest(command)

    def test_200_bad_controller(self):
        command = ["add_disk", "--machine=ut3c5n10", "--disk=sdc",
                   "--controller=controller-does-not-exist", "--size=34"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "controller-does-not-exist is not a valid "
                         "controller type",
                         command)

    def test_200_duplicate_disk(self):
        command = ["add", "disk", "--machine", "ut3c5n10", "--disk", "sdb",
                   "--controller", "scsi", "--size", "34"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 already has a disk named sdb.",
                         command)

    def test_200_extra_boot_disk(self):
        command = ["add", "disk", "--machine", "ut3c5n10", "--disk", "sdc",
                   "--controller", "scsi", "--size", "34", "--boot"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 already has a boot disk.",
                         command)

    def test_200_bad_address(self):
        command = ["add_disk", "--machine=ut3c5n10", "--disk=sdc",
                   "--controller=scsi", "--size=34",
                   "--address", "bad-address"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         r"Disk address 'bad-address' is not valid, it must "
                         r"match (?:\d+:){3}\d+$.",
                         command)

    def test_300_show_ut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Disk: sda 68 GB scsi (local) [boot]", command)
        self.searchoutput(out,
                          r"Disk: sdb 34 GB scsi \(local\)\s*"
                          r"Address: 0:0:1:0\s*"
                          r"Comments: Disk comments",
                          command)

    def test_300_cat_ut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"harddisks/{sda}" = '
                          r'create\("hardware/harddisk/generic/scsi",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 68\*GB,\s*'
                          r'"interface", "scsi"\s*\);',
                          command)
        self.searchoutput(out,
                          r'"harddisks/{sdb}" = '
                          r'create\("hardware/harddisk/generic/scsi",\s*'
                          r'"address", "0:0:1:0",\s*'
                          r'"capacity", 34\*GB,\s*'
                          r'"interface", "scsi"\s*\);',
                          command)

    def test_300_show_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Disk: sda 68 GB scsi (local) [boot]", command)
        self.searchoutput(out,
                          r'Disk: c0d0 34 GB cciss \(local\)$'
                          r'\s*WWN: 600508b112233445566778899aabbccd$'
                          r'\s*Controller Bus Address: pci:0000:01:00.0',
                          command)

    def test_300_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"harddisks/{cciss/c0d0}" = '
                          r'create\("hardware/harddisk/generic/cciss",\s*'
                          r'"bus", "pci:0000:01:00.0",\s*'
                          r'"capacity", 34\*GB,\s*'
                          r'"interface", "cciss",\s*'
                          r'"wwn", "600508b112233445566778899aabbccd"\s*\);',
                          command)
        self.searchoutput(out,
                          r'"harddisks/{sda}" = '
                          r'create\("hardware/harddisk/generic/scsi",\s*'
                          r'"boot", true,\s*'
                          r'"capacity", 68\*GB,\s*'
                          r'"interface", "scsi"\s*\);',
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
