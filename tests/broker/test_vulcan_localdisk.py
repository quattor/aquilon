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
"""Module for testing the vulcan2 related commands."""

from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestVulcanLocalDisk(VerifyNotificationsMixin, TestBrokerCommand):

    def test_070_try_delete_vmhost(self):
        command = ["del_host", "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host evh82.aqd-unittest.ms.com still has virtual "
                         "machines: evm50, evm51, evm52.",
                         command)

    def test_122_addvmfswohost(self):
        # Try to bind to fs1 of another host.
        command = ["add", "disk", "--machine", "evm50",
                   "--disk", "sdb", "--controller", "scsi",
                   "--filesystem", "utfs1n", "--address", "0:1",
                   "--size", "34"]

        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host evh82.aqd-unittest.ms.com does not have "
                         "filesystem utfs1n assigned to it.",
                         command)

    def test_156_del_used_filesystem(self):
        command = ["del_filesystem", "--filesystem", "utfs1",
                   "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Filesystem utfs1 has virtual disks attached, "
                         "so it cannot be deleted.", command)

    def test_210_move_machine(self):
        old_path = ["machine", "americas", "ut", "ut3", "ut14s1p2"]
        new_path = ["machine", "americas", "ut", "ut14", "ut14s1p2"]

        self.check_plenary_exists(*old_path)
        self.check_plenary_gone(*new_path)
        self.noouttest(["update", "machine", "--machine", "ut14s1p2",
                        "--rack", "ut14"])
        self.check_plenary_gone(*old_path)
        self.check_plenary_exists(*new_path)

    def test_220_check_location(self):
        command = ["show", "machine", "--machine", "ut14s1p2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut14", command)

    def test_230_check_vm_location(self):
        for i in range(0, 3):
            machine = "evm%d" % (i + 50)
            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)
            self.matchoutput(out, "Rack: ut14", command)

    # Move uptpgm back and forth
    def test_240_fail_move_vm_disks(self):
        command = ["update_machine", "--machine", "evm50",
                   "--cluster", "utecl15"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl15 does not have filesystem utfs1 "
                         "assigned to it.",
                         command)

    def test_241_move_remap_disk(self):
        net = self.net["autopg2"]
        ip = self.net["utpgsw0-v710"].usable[0]
        command = ["update_machine", "--machine", "evm50",
                   "--vmhost", "evh83.aqd-unittest.ms.com",
                   "--remap_disk", "filesystem/utfs1:filesystem/utrg2/utfs2"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Warning: public interface eth0 of machine "
                         "evm50.aqd-unittest.ms.com is bound to network "
                         "autopg2 [%s] due to port group user-v710, which "
                         "does not contain IP address %s." %
                         (net, ip),
                         command)

        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh83.aqd-unittest.ms.com", command)
        self.matchoutput(out, "stored on filesystem utfs2", command)

    def test_242_convert_to_share(self):
        net = self.net["autopg2"]
        ip = self.net["utpgsw0-v710"].usable[0]
        command = ["update_machine", "--machine", "evm50",
                   "--remap_disk", "filesystem/utrg2/utfs2:share/utrg2/test_v2_share"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Warning: public interface eth0 of machine "
                         "evm50.aqd-unittest.ms.com is bound to network "
                         "autopg2 [%s] due to port group user-v710, which "
                         "does not contain IP address %s." %
                         (net, ip),
                         command)

        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh83.aqd-unittest.ms.com", command)
        self.matchoutput(out, "stored on share test_v2_share", command)

    def test_243_move_back(self):
        command = ["update_machine", "--machine", "evm50",
                   "--vmhost", "evh82.aqd-unittest.ms.com",
                   "--remap_disk", "share/utrg2/test_v2_share:filesystem/utfs1"]
        self.statustest(command)

        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh82.aqd-unittest.ms.com", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcanLocalDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
