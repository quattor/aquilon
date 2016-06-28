#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
'Module for testing moving VMs around.'

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestVMMigration(TestBrokerCommand):

    def test_100_metacluster_change_pre(self):
        command = ["show_share", "--all"]
        out = self.commandtest(command)
        # Initially the VM is on utecl1, test_share_1 is not used on utecl11
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl1\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 1\s*'
                          r'Machine Count: 1\s*',
                          command)
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl11\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 0\s*'
                          r'Machine Count: 0\s*',
                          command)

    def test_101_metacluster_change(self):
        old_path = ["machine", "americas", "ut", "ut10", "evm1"]
        new_path = ["machine", "americas", "ut", "None", "evm1"]
        command = ["update_machine", "--machine=evm1", "--cluster=utecl11",
                   "--allow_metacluster_change"]
        self.noouttest(command)
        self.check_plenary_gone(*old_path)
        self.check_plenary_exists(*new_path)

    def test_105_verify_shares(self):
        command = ["show_share", "--all"]
        out = self.commandtest(command)

        # The disk should have moved to utecl11, test_share_1 should be unused on
        # utecl1
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl1\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 0\s*'
                          r'Machine Count: 0\s*',
                          command)
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl11\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 1\s*'
                          r'Machine Count: 1\s*',
                          command)

    def test_105_verify_search_machine(self):
        command = ["search_machine", "--machine=evm1", "--cluster=utecl11"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm1", command)

    def test_109_revert_metacluster_change(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl1",
                   "--allow_metacluster_change"]
        # restore
        self.noouttest(command)

    def test_110_verify_status_quo(self):
        command = ["show_machine", "--machine", "evm40"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl12", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$",
                          command)

    def test_111_move_machine(self):
        # Moving the machine from one cluster to the other exercises the case in
        # the disk movement logic when the old share is inside a resource group.
        command = ["update_machine", "--machine", "evm40",
                   "--cluster", "utecl13"]
        self.noouttest(command)

    def test_115_verify_move(self):
        command = ["show_machine", "--machine", "evm40"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl13", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$",
                          command)

    def test_120_fail_move_vm_disks(self):
        # This should fail without --remap_disk
        command = ["update_machine", "--machine", "evm50",
                   "--cluster", "utecl15"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl15 does not have filesystem utfs1 "
                         "assigned to it.",
                         command)

    def test_121_move_remap_disk(self):
        command = ["update_machine", "--machine", "evm50",
                   "--vmhost", "evh83.aqd-unittest.ms.com",
                   "--remap_disk", "filesystem/utfs1:filesystem/utrg2/utfs2"]
        self.noouttest(command)

        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh83.aqd-unittest.ms.com", command)
        self.matchoutput(out, "stored on filesystem utfs2", command)

    def test_122_convert_to_share(self):
        command = ["update_machine", "--machine", "evm50",
                   "--remap_disk", "filesystem/utrg2/utfs2:share/utrg2/test_v2_share"]
        self.noouttest(command)

        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh83.aqd-unittest.ms.com", command)
        self.matchoutput(out, "stored on share test_v2_share", command)

    def test_123_move_back(self):
        command = ["update_machine", "--machine", "evm50",
                   "--vmhost", "evh82.aqd-unittest.ms.com",
                   "--remap_disk", "share/utrg2/test_v2_share:filesystem/utfs1"]
        self.noouttest(command)

        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh82.aqd-unittest.ms.com", command)

    def test_130_make_room(self):
        self.noouttest(["del_interface", "--machine", "evm41", "--interface", "eth0"])

    def test_132_pg_move_autoip(self):
        self.dsdb_expect_update("evm50.aqd-unittest.ms.com", "eth0",
                                self.net["autopg1"].usable[0])
        command = ["update_machine", "--machine", "evm50",
                   "--cluster", "utecl13", "--allow_metacluster_change",
                   "--remap_disk", "filesystem/utfs1:share/utmc8as1/test_v2_share",
                   "--autoip"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_135_show_evm50(self):
        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl13", command)
        self.matchoutput(out,
                         "Primary Name: evm50.aqd-unittest.ms.com [%s]" %
                         self.net["autopg1"].usable[0],
                         command)

    def test_135_autopg1(self):
        net = self.net["autopg1"]
        command = ["search_machine", "--networkip", net.ip]
        out = self.commandtest(command)
        self.matchoutput(out, "evm50", command)

    def test_135_autopg2(self):
        # This verifies that the port group binding is gone
        net = self.net["autopg2"]
        command = ["search_machine", "--networkip", net.ip]
        out = self.commandtest(command)
        self.matchclean(out, "evm50", command)

    def test_136_move_back(self):
        ip = self.net["autopg2"].usable[0]
        self.dsdb_expect_update("evm50.aqd-unittest.ms.com", "eth0", ip)
        command = ["update_machine", "--machine", "evm50",
                   "--vmhost", "evh82.aqd-unittest.ms.com",
                   "--allow_metacluster_change",
                   "--remap_disk", "share/utmc8as1/test_v2_share:filesystem/utfs1",
                   "--autoip"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_137_show_evm50(self):
        command = ["show_machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh82.aqd-unittest.ms.com", command)
        self.matchoutput(out,
                         "Primary Name: evm50.aqd-unittest.ms.com [%s]" %
                         self.net["autopg2"].usable[0],
                         command)

    def test_137_autopg1(self):
        net = self.net["autopg1"]
        command = ["search_machine", "--networkip", net.ip]
        out = self.commandtest(command)
        self.matchclean(out, "evm50", command)

    def test_137_autopg2(self):
        net = self.net["autopg2"]
        command = ["search_machine", "--networkip", net.ip]
        out = self.commandtest(command)
        self.matchoutput(out, "evm50", command)

    def test_138_restore_evm41(self):
        self.noouttest(["add_interface", "--machine", "evm41",
                        "--interface", "eth0", "--automac", "--autopg"])

    def test_200_missing_cluster(self):
        command = ["update_machine", "--machine=evm1",
                   "--cluster=cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def test_200_change_metacluster(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl11"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Moving VMs between metaclusters is disabled by "
                         "default.",
                         command)

    def test_200_cluster_full(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl3"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl3 cannot support VMs with "
                         "0 vmhosts and a down_hosts_threshold of 2",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVMMigration)
    unittest.TextTestRunner(verbosity=2).run(suite)
