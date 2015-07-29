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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestVulcan20(VerifyNotificationsMixin, TestBrokerCommand):

    def add_utcluster(self, name, metacluster):
        command = ["add_esx_cluster", "--cluster=%s" % name,
                   "--metacluster=%s" % metacluster, "--room=utroom1",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan2-server-dev"]
        self.noouttest(command)

    def test_090_addmachines(self):
        for i in range(0, 3):
            cluster = "utecl%d" % (i // 2 + 12)
            machine = "utpgm%d" % i

            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", cluster, "--model", "utmedium"])

    def test_097_search_machine_by_metacluster(self):
        command = "search machine --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgm0", command)
        self.matchoutput(out, "utpgm1", command)
        self.matchoutput(out, "utpgm2", command)
        self.matchclean(out, "ut14s1p0", command)

    # Autopg test
    def test_130_addinterfaces(self):
        self.noouttest(["add", "interface", "--machine", "utpgm0",
                        "--interface", "eth0", "--automac", "--autopg"])

        # Consume available IP addresses
        self.dsdb_expect_add("utpgm0-ip1.aqd-unittest.ms.com",
                             self.net["autopg1"].usable[0], "eth0_ip1")
        self.dsdb_expect_add("utpgm0-ip2.aqd-unittest.ms.com",
                             self.net["autopg1"].usable[1], "eth0_ip2")
        self.noouttest(["add_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip1", "--autoip",
                        "--fqdn", "utpgm0-ip1.aqd-unittest.ms.com"])
        self.noouttest(["add_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip2", "--autoip",
                        "--fqdn", "utpgm0-ip2.aqd-unittest.ms.com"])
        self.dsdb_verify()

        # All IPs gone, this should fail
        command = ["add", "interface", "--machine", "utpgm1",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on virtual switch "
                         "utvswitch.",
                         command)

        # Free up the IP addresses
        self.dsdb_expect_delete(self.net["autopg1"].usable[0])
        self.dsdb_expect_delete(self.net["autopg1"].usable[1])
        self.noouttest(["del_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip1"])
        self.noouttest(["del_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip2"])
        self.dsdb_verify()

        # There's just one pg, so this should fail
        command = ["add_interface", "--machine", "utpgm0",
                   "--interface", "eth1", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on virtual switch "
                         "utvswitch.",
                         command)

        # Now it should succeed
        self.noouttest(["add", "interface", "--machine", "utpgm1",
                        "--interface", "eth0", "--automac", "--autopg"])

        # The third one shall fail
        command = ["add", "interface", "--machine", "utpgm2",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on virtual switch "
                         "utvswitch.",
                         command)

    def test_140_verify_audit(self):
        command = ["search_audit", "--command", "add_interface",
                   "--keyword", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "pg=user-v710", command)

    def test_260_search_metacluster_by_share(self):
        command = ["search_metacluster", "--share", "test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def test_265_search_cluster_by_share(self):
        self.noouttest(["search_cluster", "--share", "test_v2_share"])

    # disk tests
    def test_300_add_disk_to_share(self):
        for i in range(0, 3):
            self.noouttest(["add", "disk", "--machine", "utpgm%d" % i,
                            "--disk", "sda", "--controller", "scsi",
                            "--snapshot", "--share", "test_v2_share",
                            "--size", "34", "--resourcegroup", "utmc8as1",
                            "--address", "0:0", "--iops_limit", "20"])

    def test_305_search_machine_by_share(self):
        command = ["search_machine", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utpgm0", command)
        self.matchclean(out, "evm2", command)
        self.matchclean(out, "evm10", command)

    def test_310_verify_add_disk_to_share(self):
        command = "show machine --machine utpgm0"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$", command)
        self.searchoutput(out, r"IOPS Limit: 20", command)

        command = ["show_machine", "--machine", "utpgm0", "--format", "proto"]
        machine = self.protobuftest(command, expect=1)[0]
        self.assertEqual(machine.name, "utpgm0")
        self.assertEqual(len(machine.disks), 1)
        self.assertEqual(machine.disks[0].device_name, "sda")
        self.assertEqual(machine.disks[0].disk_type, "scsi")
        self.assertEqual(machine.disks[0].capacity, 34)
        self.assertEqual(machine.disks[0].address, "0:0")
        self.assertEqual(machine.disks[0].bus_address, "")
        self.assertEqual(machine.disks[0].wwn, "")
        self.assertEqual(machine.disks[0].snapshotable, True)
        self.assertEqual(machine.disks[0].backing_store.name, "test_v2_share")
        self.assertEqual(machine.disks[0].backing_store.type, "share")
        self.assertEqual(machine.disks[0].iops_limit, 20)
        self.assertEqual(machine.vm_host.fqdn, "")
        self.assertEqual(machine.vm_cluster.name, "utecl12")
        self.assertEqual(machine.vm_cluster.metacluster, "utmc8")

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Disk Count: 3", command)

        command = ["cat", "--machine", "utpgm0", "--generate"]

        out = self.commandtest(command)
        self.matchoutput(out, '"harddisks/{sda}" = nlist(', command)
        self.searchoutput(out,
                          r'"mountpoint", "/vol/lnn30f1v1/test_v2_share",\s*'
                          r'"path", "utpgm0/sda.vmdk",\s*'
                          r'"server", "lnn30f1",\s*'
                          r'"sharename", "test_v2_share",\s*'
                          r'"snapshot", true',
                          command)

    # machine move tests
    def test_350_move_machine_pre(self):
        command = ["show_machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl12", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$",
                          command)

    def test_360_move_machine(self):
        # Moving the machine from one cluster to the other exercises the case in
        # the disk movement logic when the old share is inside a resource group.
        command = ["update_machine", "--machine", "utpgm0",
                   "--cluster", "utecl13"]
        self.noouttest(command)

    def test_370_verify_move(self):
        command = ["show_machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl13", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$",
                          command)

    def test_380_fail_update_disk(self):
        command = ["update_disk", "--disk", "sda", "--machine", "utpgm0",
                   "--share", "non_existent_share",
                   "--resourcegroup", "utmc8as1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl13 does not have share "
                         "non_existent_share assigned to it in "
                         "resourcegroup utmc8as1.",
                         command)

#    metacluster aligned svc tests
    def test_400_addvcenterservices(self):
        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

    def test_410_bindvcenterservices(self):
        command = ["bind_client", "--metacluster", "utmc8",
                   "--service", "vcenter", "--instance", "ut"]
        err = self.statustest(command)
        # The service should be bound to the metacluster and to the hosts, but
        # not to the clusters as they do not require it
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service instance vcenter/ut", command)
        self.matchoutput(err, "Host evh80.aqd-unittest.ms.com adding binding "
                         "for service instance vcenter/ut", command)
        self.matchoutput(err, "Host evh81.aqd-unittest.ms.com adding binding "
                         "for service instance vcenter/ut", command)
        self.matchclean(err, "utecl", command)

        command = ["show", "host", "--hostname", "evh80.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Uses Service: vcenter Instance: ut",
                         command)

        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Member Alignment: Service vcenter Instance ut", command)

    def test_420_failmaxclientcount(self):
        command = ["update_service", "--service", "vcenter", "--instance", "ut",
                   "--max_clients", "17"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut"]
        self.noouttest(command)

        self.add_utcluster("utpgcl2", "utmc8")

        command = ["make", "cluster", "--cluster", "utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Please use the --metacluster option for "
                         "metaclusters.", command)
        self.matchoutput(out,
                         "The available instances ['ut'] for service vcenter "
                         "are at full capacity.",
                         command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut"]
        self.noouttest(command)

        self.statustest(["del_cluster", "--cluster=utpgcl2"])

    def test_430_unbindvcenterservices(self):
        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
        self.noouttest(command)

        self.noouttest(["unbind_client", "--metacluster", "utmc8",
                        "--service", "vcenter"])

    def test_440_unmapvcenterservices(self):
        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut",
                   "--personality", "vulcan2-server-dev", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["make", "--hostname", "evh80.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host evh80.aqd-unittest.ms.com removing "
                         "binding for service instance vcenter/ut", command)

        command = ["show", "host", "--hostname", "evh80.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out,
                        "Uses Service: vcenter Instance: ut",
                        command)

    #
    # service binding conflicts
    #
    def test_500_add_mc_esx_service(self):
        command = ["add", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["rebind_client", "--metacluster", "utmc8",
                   "--service", "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Metacluster utmc8 adding binding for service "
                         "instance esx_management_server/ut.mc",
                         command)
        for cluster in ["utecl12", "utecl13"]:
            self.searchoutput(err,
                              "ESX Cluster %s removing binding for service "
                              "instance esx_management_server/ut.[ab]" % cluster,
                              command)
            self.matchoutput(err,
                             "ESX Cluster %s adding binding for service "
                             "instance esx_management_server/ut.mc" % cluster,
                             command)
        for host in ["evh80", "evh81"]:
            self.searchoutput(err,
                              "Host %s.aqd-unittest.ms.com removing binding for "
                              "service instance esx_management_server/ut.[ab]" % host,
                              command)
            self.matchoutput(err,
                             "Host %s.aqd-unittest.ms.com adding binding for "
                             "service instance esx_management_server/ut.mc" % host,
                             command)

    def test_510_fail_make_host(self):
        command = ["make", "--hostname", "evh80.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for "
                         "host evh80.aqd-unittest.ms.com.",
                         command)

    def test_510_fail_make_cluster(self):
        command = ["make", "cluster", "--cluster", "utecl12"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for ESX cluster utecl12.",
                         command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for "
                         "host evh80.aqd-unittest.ms.com.",
                         command)

    def test_520_verify_client_count(self):
        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 16$", command)

    def test_530_verify_mixed_client_count(self):
        self.add_utcluster("utpgcl3", "utmc8")
        command = ["bind_client", "--cluster", "utpgcl3", "--service",
                   "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "ESX Cluster utpgcl3 adding binding for service "
                         "instance esx_management_server/ut.mc", command)

        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 24$", command)

        # Can't unbind an an aligned service here and don't want unalign it

    def test_538_del_utpgcl3(self):
        self.statustest(["del_cluster", "--cluster=utpgcl3"])

    def test_540_remove_mc_esx_service(self):
        command = ["del_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["unbind_client", "--metacluster", "utmc8",
                   "--service", "esx_management_server"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        out = self.statustest(["make_cluster", "--cluster", "utecl12"])
        self.matchoutput(out, "removing binding for service instance "
                         "esx_management_server/ut.mc", command)
        self.searchoutput(out, "adding binding for service instance "
                          "esx_management_server/ut.[ab]", command)
        out = self.statustest(["make_cluster", "--cluster", "utecl13"])
        self.matchoutput(out, "removing binding for service instance "
                         "esx_management_server/ut.mc", command)
        self.searchoutput(out, "adding binding for service instance "
                          "esx_management_server/ut.[ab]", command)

        command = ["del", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

    def test_600_delutpgmdisk(self):
        for i in range(0, 3):
            self.noouttest(["del_disk", "--machine", "utpgm%d" % i, "--disk", "sda"])

    def test_710_delmachines(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            self.noouttest(["del", "machine", "--machine", machine])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcan20)
    unittest.TextTestRunner(verbosity=2).run(suite)
