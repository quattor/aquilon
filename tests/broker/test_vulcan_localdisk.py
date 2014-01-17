#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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

import os
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin
from machinetest import MachineTestMixin
from personalitytest import PersonalityTestMixin


class TestVulcanLocalDisk(VerifyNotificationsMixin, MachineTestMixin,
                          PersonalityTestMixin, TestBrokerCommand):

    metacluster = "utmc9"
    cluster = ["utlccl0", "utlccl1"]
    switch = ["utpgsw0.aqd-unittest.ms.com", "utpgsw1.aqd-unittest.ms.com"]
    vmhost = ["utpgh0.aqd-unittest.ms.com", "utpgh1.aqd-unittest.ms.com"]
    machine = ["utpgs01p0", "utpgs01p1"]

    def getip(self):
        return self.net["autopg2"].usable[0]

    def test_000_add_vlocal(self):
        maps = {
            "esx_management_server": {
                "ut.a": {
                    "building": ["ut"],
                },
            },
        }

        self.create_personality("vmhost", "vulcan-local-disk",
                                grn="grn:/ms/ei/aquilon/aqd", maps=maps,
                                required=["esx_management_server"])
        self.create_personality("esx_cluster", "vulcan-local-disk",
                                grn="grn:/ms/ei/aquilon/aqd", maps=maps)
        self.create_personality("aquilon", "virteng-perf-test",
                                grn="grn:/ms/ei/aquilon/aqd")
        # FIXME: Localdisk setups should not have a metacluster, but the
        # templates expect one to exist
        self.create_personality("metacluster", "vulcan-local-disk")

    def test_005_addutmc9(self):
        command = ["add_metacluster", "--metacluster=%s" % self.metacluster,
                   "--personality=vulcan-local-disk", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut", "--domain=unittest",
                   "--comments=vulcan_localdisk_test"]
        self.noouttest(command)

    # INFO: this piece of code is needed to make autopg logic work for vulcan
    # localdisk, too.
    # TODO we may want to use the actual vulcal local disk cluster personality,
    # it removes the clusterreg part.
    def test_010_addutlccl1(self):
        for i in range(0, 2):
            command = ["add_esx_cluster", "--cluster=%s" % self.cluster[i],
                       "--metacluster=%s" % self.metacluster, "--room=utroom1",
                       "--buildstatus=build",
                       "--domain=unittest", "--down_hosts_threshold=0",
                       "--archetype=esx_cluster",
                       "--personality=vulcan-local-disk"]
            self.noouttest(command)

    # reusing vulcan2 subnets here.
    def test_020_addutpgsw(self):
        for i in range(0, 2):
            ip = self.net["autopg1"].usable[i]

            self.dsdb_expect_add(self.switch[i], ip, "xge49",
                                 ip.mac)
            command = ["add", "network_device", "--network_device", self.switch[i],
                       "--rack", "ut12",
                       "--model", "rs g8000", "--interface", "xge49",
                       "--type", "tor", "--mac", ip.mac, "--ip", ip]
            (out, err) = self.successtest(command)
        self.dsdb_verify()

    # see fakevlan2net
    def test_025_pollutpgsw(self):

        for i in range(0, 2):
            command = ["poll", "network_device", "--vlan", "--network_device",
                       self.switch[i]]
            (out, err) = self.successtest(command)

            service = self.config.get("broker", "poll_helper_service")
            self.matchoutput(err,
                             "Using jump host nyaqd1.ms.com from service "
                             "instance %s/unittest to run discovery "
                             "for switch %s" % (service, self.switch[i]),
                             command)

        # For Nexus switches we have if names, not snmp ids.
        # Checking only the first one
        command = "show network_device --network_device %s" % self.switch[1]
        out = self.commandtest(command.split(" "))

        macs = ["02:02:04:02:12:06", "02:02:04:02:12:07"]
        for i in range(0, 2):
            self.matchoutput(out, "Port et1-%d: %s" % (i + 1, macs[i]), command)

    def test_030_addswitch(self):
        for i in range(0, 2):
            self.successtest(["update_esx_cluster",
                              "--cluster=%s" %self.cluster[i],
                              "--switch=%s" % self.switch[i]])

    def test_050_add_vmhost(self):
        for i in range(0, 2):
            ip = self.net["autopg2"].usable[i]

            self.create_host(self.vmhost[i], ip, self.machine[i],
                             model="vb1205xm", rack="ut3",
                             archetype="vmhost", personality="vulcan-local-disk",
                             osname="esxi", osversion="4.0.0")

    def test_060_bind_host_to_cluster(self):
        for i in range(0, 2):
            self.successtest(["make", "cluster", "--cluster", self.cluster[i]])

            self.successtest(["cluster",
                              "--hostname", self.vmhost[i], "--cluster", self.cluster[i]])

    def test_065_add_vms(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            command = ["add", "machine", "--machine", machine,
                       "--vmhost", self.vmhost[0], "--model", "utmedium"]
            self.noouttest(command)

    def test_120_cat_vmhost(self):
        command = ["cat", "--hostname=%s" % self.vmhost[0], "--generate", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "template hostdata/%s;" % self.vmhost[0],
                         command)
        self.matchoutput(out,
                         '"system/resources/virtual_machine" '
                         '= append(create("resource/host/%s/'
                         'virtual_machine/utpgm0/config"));' % self.vmhost[0],
                         command)

    def test_122_addvmfswohost(self):
        # Try to bind to fs1 of another host.
        command = ["add", "disk", "--machine", "utpgm0",
                   "--disk", "sda", "--controller", "scsi",
                   "--filesystem", "utfs1n", "--address", "0:0",
                   "--size", "34"]

        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Not Found: Filesystem utfs1n, hostresource instance not found.",
                         command)

    def test_125_addvmfs(self):
        command = ["add_filesystem", "--filesystem=utfs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--hostname=%s" % self.vmhost[0]]
        self.successtest(command)

        # Quick test
        command = ["cat", "--filesystem=utfs1",
                   "--hostname=%s" % self.vmhost[0]]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "utfs1";', command)

    def test_130_addutpgm0disk(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i
            self.noouttest(["add", "disk", "--machine", machine,
                            "--disk", "sda", "--controller", "scsi",
                            "--filesystem", "utfs1", "--address", "0:0",
                            "--size", "34"])

    def test_140_verifyaddutpgm0disk(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)

            self.searchoutput(out, r"Disk: sda 34 GB scsi \(virtual_localdisk from utfs1\) \[boot\]$",
                              command)

        command = ["cat", "--machine", "utpgm0", "--generate"]
        out = self.commandtest(command)
        self.matchclean(out, "snapshot", command)

    def test_150_verifyutfs1(self):
        command = ["show_filesystem", "--filesystem=utfs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: utfs1", command)
        self.matchoutput(out, "Bound to: Host %s" % self.vmhost[0], command)
        self.matchoutput(out, "Virtual Disk Count: 3", command)


    def test_155_catutpgm0(self):
        command = ["cat", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, '', command)
        self.matchoutput(out, '"filesystemname", "utfs1",', command)
        self.matchoutput(out, '"mountpoint", "/mnt",', command)
        self.matchoutput(out, '"path", "utpgm0/sda.vmdk"', command)


    def test_160_addinterfaces(self):
        # TODO: fixed mac addresses grabbed from test_vulcan2 until automac\pg
        # for localdisk is implemented.

        # Pick first one with automac(fakebind data should be fixed)
        for i in range(0, 2):
            self.noouttest(["add", "interface", "--machine", "utpgm%d" % i,
                            "--interface", "eth0", "--automac", "--autopg"])

    def test_170_add_vm_hosts(self):
        ip = self.net["utpgsw0-v710"].usable[0]
        self.dsdb_expect_add("utpgm0.aqd-unittest.ms.com", ip, "eth0", "00:50:56:01:20:00" )
        command = ["add", "host", "--hostname", "utpgm0.aqd-unittest.ms.com",
                   "--ip", ip,
                   "--machine", "utpgm0",
                   "--domain", "unittest", "--buildstatus", "build",
                   "--archetype", "aquilon",
                   "--personality", "virteng-perf-test"]
        self.noouttest(command)
        self.dsdb_verify()


    def test_175_make_vm_host(self):
        basetime = datetime.now()
        command = ["make", "--hostname", "utpgm0.aqd-unittest.ms.com"]
        self.successtest(command)
        self.wait_notification(basetime, 1)

        command = ["show", "host", "--hostname", "utpgm0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        #TODO what to test here?
        # self.matchclean(out, "Template: service/vcenter/ut", command)

    def test_200_make_host(self):
        basetime = datetime.now()
        command = ["make", "--hostname", self.vmhost[0]]
        self.successtest(command)
        self.wait_notification(basetime, 1)

        command = ["show", "host", "--hostname", self.vmhost[0]]
        out = self.commandtest(command)
        self.matchclean(out, "Uses Sertice: vcenter Instance: ut", command)

    def check_path_exclusive(self, path, wrongpath):
        self.failIf(os.path.exists(wrongpath),
                    "Plenary file '%s' not removed." % wrongpath)
        self.failUnless(os.path.exists(path),
                        "Plenary file '%s' not created." % path)

    def test_210_move_machine(self):
        # self.plenary_core = "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__
        oldpath = self.plenary_name("machine", "americas", "ut", "ut3", self.machine[0])
        newpath = self.plenary_name("machine", "americas", "ut", "ut13", self.machine[0])

        self.check_path_exclusive(oldpath, newpath)
        self.noouttest(["update", "machine", "--machine", self.machine[0],
                        "--rack", "ut13"])
        self.check_path_exclusive(newpath, oldpath)

    def test_220_check_location(self):
        command = ["show", "machine", "--machine", self.machine[0]]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut13", command)

    def test_230_check_vm_location(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i
            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)
            self.matchoutput(out, "Rack: ut13", command)


    # Move uptpgm back and forth utpg0 / utlccl2
    def test_240_fail_move_vm_disks(self):
        command = ["update_machine", "--machine", "utpgm0",
                   "--cluster", "utlccl1"]
        out = self.badrequesttest(command)
    # TODO to be replaced with some other error message.
        self.matchoutput(out,
                         "ESX Cluster utlccl1 does not have filesystem utfs1 "
                         "assigned to it.",
                         command)

    # deletes

    def test_250_delutpgm0disk(self):
        for i in range(0, 3):
            self.noouttest(["del", "disk", "--machine", "utpgm%d" % i,
                            "--controller", "scsi", "--disk", "sda"])

    def test_260_move_vm_to_cluster(self):
        self.noouttest(["update", "machine", "--machine", "utpgm0",
                        "--cluster", "utlccl1"])

        command = ["show", "machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utlccl1", command)

    def test_270_move_vm_to_vmhost(self):
        self.noouttest(["update", "machine", "--machine", "utpgm0",
                        "--vmhost", self.vmhost[0]])

        command = ["show", "machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: Host utpgh0.aqd-unittest.ms.com",
                         command)


    # deleting fs before depending disk would drop them as well
    def test_295_delvmfs(self):
        command = ["del_filesystem", "--filesystem=utfs1",
                   "--hostname=%s" % self.vmhost[0]]
        self.successtest(command)

    def test_305_del_vm_host(self):
        basetime = datetime.now()
        ip = self.net["utpgsw0-v710"].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "host", "--hostname", "utpgm0.aqd-unittest.ms.com"]
        self.statustest(command)
        self.wait_notification(basetime, 1)
        self.dsdb_verify()

    def test_310_del_vms(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            self.noouttest(["del", "machine", "--machine", machine])

    def test_320_del_vmhost(self):
        for i in range(0, 2):
            ip = self.net["autopg2"].usable[i]
            basetime = datetime.now()
            self.dsdb_expect_delete(ip)
            command = ["del", "host", "--hostname", self.vmhost[i]]
            self.statustest(command)
            self.wait_notification(basetime, 1)
        self.dsdb_verify()

        for i in range(0, 2):
            self.noouttest(["del", "machine", "--machine", self.machine[i]])


    def test_308_delutpgsw(self):
        for i in range(0, 2):
            ip = self.net["autopg1"].usable[i]
            plenary = self.plenary_name("switchdata", self.switch[i])
            self.failUnless(os.path.exists(plenary),
                            "Plenary file '%s' does not exist" % plenary)

            self.dsdb_expect_delete(ip)
            command = "del network_device --network_device %s" % self.switch[i]
            self.noouttest(command.split(" "))

            self.failIf(os.path.exists(plenary),
                        "Plenary file '%s' still exists" % plenary)

        self.dsdb_verify()

    def test_330_delutlccl1(self):
        for i in range(0, 2):
            command = ["del_esx_cluster", "--cluster=%s" % self.cluster[i]]
            self.successtest(command)

    def test_340_delutmc9(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=%s" % self.metacluster]
        self.statustest(command)
        self.wait_notification(basetime, 1)

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            self.metacluster + self.xml_suffix)))

    def test_500_del_vlocal(self):
        self.drop_personality("aquilon", "virteng-perf-test")
        self.drop_personality("esx_cluster", "vulcan-local-disk")
        self.drop_personality("vmhost", "vulcan-local-disk")
        self.drop_personality("metacluster", "vulcan-local-disk")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcanLocalDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
