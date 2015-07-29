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

    def test_065_add_vms(self):
        for i in range(0, 3):
            machine = "evm%d" % (i + 50)

            command = ["add", "machine", "--machine", machine,
                       "--vmhost", "evh82.aqd-unittest.ms.com", "--model", "utmedium"]
            self.noouttest(command)

    def test_070_try_delete_vmhost(self):
        command = ["del_host", "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host evh82.aqd-unittest.ms.com still has virtual "
                         "machines: evm50, evm51, evm52.",
                         command)

    def test_120_cat_vmhost(self):
        command = ["cat", "--hostname", "evh82.aqd-unittest.ms.com", "--generate", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "template hostdata/evh82.aqd-unittest.ms.com;",
                         command)
        self.matchoutput(out,
                         '"system/resources/virtual_machine" '
                         '= append(create("resource/host/evh82.aqd-unittest.ms.com/'
                         'virtual_machine/evm50/config"));',
                         command)

    def test_122_addvmfswohost(self):
        # Try to bind to fs1 of another host.
        command = ["add", "disk", "--machine", "evm50",
                   "--disk", "sda", "--controller", "scsi",
                   "--filesystem", "utfs1n", "--address", "0:0",
                   "--size", "34"]

        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host evh82.aqd-unittest.ms.com does not have "
                         "filesystem utfs1n assigned to it.",
                         command)

    def test_130_addevm50disk(self):
        for i in range(0, 3):
            machine = "evm%d" % (i + 50)
            self.noouttest(["add", "disk", "--machine", machine,
                            "--disk", "sda", "--controller", "scsi",
                            "--filesystem", "utfs1", "--address", "0:0",
                            "--size", "34"])

    def test_140_verifyaddevm50disk(self):
        for i in range(0, 3):
            machine = "evm%d" % (i + 50)

            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)

            self.searchoutput(out, r"Disk: sda 34 GB scsi \(virtual_disk stored on filesystem utfs1\) \[boot\]$",
                              command)

        command = ["cat", "--machine", "evm50", "--generate"]
        out = self.commandtest(command)
        self.matchclean(out, "snapshot", command)

    def test_141_verify_proto(self):
        command = ["show_machine", "--machine", "evm50", "--format", "proto"]
        machine = self.protobuftest(command, expect=1)[0]
        self.assertEqual(machine.name, "evm50")
        self.assertEqual(len(machine.disks), 1)
        self.assertEqual(machine.disks[0].device_name, "sda")
        self.assertEqual(machine.disks[0].disk_type, "scsi")
        self.assertEqual(machine.disks[0].capacity, 34)
        self.assertEqual(machine.disks[0].address, "0:0")
        self.assertEqual(machine.disks[0].bus_address, "")
        self.assertEqual(machine.disks[0].wwn, "")
        self.assertEqual(machine.disks[0].snapshotable, False)
        self.assertEqual(machine.disks[0].backing_store.name, "utfs1")
        self.assertEqual(machine.disks[0].backing_store.type, "filesystem")
        self.assertEqual(machine.vm_cluster.name, "")
        self.assertEqual(machine.vm_host.hostname, "evh82")
        self.assertEqual(machine.vm_host.fqdn, "evh82.aqd-unittest.ms.com")
        self.assertEqual(machine.vm_host.dns_domain, "aqd-unittest.ms.com")

    def test_145_search_machine_filesystem(self):
        command = ["search_machine", "--disk_filesystem", "utfs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm50", command)
        self.matchoutput(out, "evm51", command)
        self.matchoutput(out, "evm52", command)
        self.matchclean(out, "evm1", command)
        self.matchclean(out, "evm2", command)
        self.matchclean(out, "evm4", command)
        self.matchclean(out, "ut3", command)
        self.matchclean(out, "ut5", command)

    def test_150_verifyutfs1(self):
        command = ["show_filesystem", "--filesystem=utfs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: utfs1", command)
        self.matchoutput(out, "Bound to: Host evh82.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Virtual Disk Count: 3", command)

    def test_155_catevm50(self):
        command = ["cat", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, '', command)
        self.matchoutput(out, '"filesystemname", "utfs1",', command)
        self.matchoutput(out, '"mountpoint", "/mnt",', command)
        self.matchoutput(out, '"path", "evm50/sda.vmdk"', command)

    def test_156_del_used_filesystem(self):
        command = ["del_filesystem", "--filesystem", "utfs1",
                   "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Filesystem utfs1 has virtual disks attached, "
                         "so it cannot be deleted.", command)

    def test_160_addinterfaces(self):
        # TODO: fixed mac addresses grabbed from test_vulcan2 until automac\pg
        # for localdisk is implemented.

        # Pick first one with automac(fakebind data should be fixed)
        for i in range(0, 2):
            self.noouttest(["add", "interface", "--machine", "evm%d" % (i + 50),
                            "--interface", "eth0", "--automac", "--autopg"])

    def test_170_add_vm_hosts(self):
        net = self.net["autopg2"]
        ip = self.net["utpgsw0-v710"].usable[0]
        self.dsdb_expect_add("evm50.aqd-unittest.ms.com", ip, "eth0", "00:50:56:01:20:00")
        command = ["add", "host", "--hostname", "evm50.aqd-unittest.ms.com",
                   "--ip", ip,
                   "--machine", "evm50",
                   "--domain", "unittest", "--buildstatus", "build",
                   "--archetype", "aquilon",
                   "--personality", "unixeng-test"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Warning: public interface eth0 of machine "
                         "evm50.aqd-unittest.ms.com is bound to network "
                         "autopg2 [%s] due to port group user-v710, which "
                         "does not contain IP address %s." %
                         (net, ip),
                         command)
        self.dsdb_verify()

    def test_175_make_vm_host(self):
        basetime = datetime.now()
        command = ["make", "--hostname", "evm50.aqd-unittest.ms.com"]
        self.statustest(command)
        self.wait_notification(basetime, 1)

        command = ["show", "host", "--hostname", "evm50.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh82.aqd-unittest.ms.com", command)

    def test_200_make_host(self):
        basetime = datetime.now()
        command = ["make", "--hostname", "evh82.aqd-unittest.ms.com"]
        self.statustest(command)
        self.wait_notification(basetime, 1)

        command = ["show", "host", "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Uses Service: vcenter Instance: ut", command)

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

    def test_250_delevm50disk(self):
        for i in range(0, 3):
            self.noouttest(["del_disk", "--machine", "evm%d" % (i + 50), "--disk", "sda"])

    def test_260_move_vm_to_cluster(self):
        self.statustest(["update", "machine", "--machine", "evm50",
                         "--cluster", "utecl15"])

        command = ["show", "machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl15", command)

    def test_265_search_machine_vmhost(self):
        command = ["search_machine", "--vmhost", "evh82.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm51", command)
        self.matchoutput(out, "evm52", command)
        self.matchclean(out, "evm50", command)

    def test_270_move_vm_to_vmhost(self):
        self.statustest(["update", "machine", "--machine", "evm50",
                         "--vmhost", "evh82.aqd-unittest.ms.com"])

        command = ["show", "machine", "--machine", "evm50"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host evh82.aqd-unittest.ms.com",
                         command)

    # deleting fs before depending disk would drop them as well
    def test_295_delvmfs(self):
        self.noouttest(["del_filesystem", "--filesystem=utfs1",
                        "--hostname=evh82.aqd-unittest.ms.com"])

    def test_305_del_vm_host(self):
        basetime = datetime.now()
        ip = self.net["utpgsw0-v710"].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "host", "--hostname", "evm50.aqd-unittest.ms.com"]
        self.statustest(command)
        self.wait_notification(basetime, 1)
        self.dsdb_verify()

    def test_310_del_vms(self):
        for i in range(0, 3):
            machine = "evm%d" % (i + 50)

            self.noouttest(["del", "machine", "--machine", machine])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcanLocalDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
