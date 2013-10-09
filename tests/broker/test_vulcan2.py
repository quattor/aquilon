#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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


class TestVulcan20(VerifyNotificationsMixin, MachineTestMixin,
                   TestBrokerCommand):
    # Metacluster / cluster / Switch tests

    def test_000_addutmc8(self):
        command = ["add_metacluster", "--metacluster=utmc8",
                   "--personality=vulcan2", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut", "--domain=unittest",
                   "--comments=autopg_v2_tests"]
        self.noouttest(command)

    def add_utcluster(self, name, metacluster):
        command = ["add_esx_cluster", "--cluster=%s" % name,
                   "--metacluster=%s" % metacluster, "--room=utroom1",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan2-10g-test"]
        self.noouttest(command)

    # see testaddutmc4
    def test_001_addutpgcl(self):
        # Allocate utecl5 - utecl10 for utmc4 (autopg testing)
        for i in range(0, 2):
            self.add_utcluster("utpgcl%d" % i, "utmc8")

    # see     def testaddut01ga2s02(self):
    def test_002_addutpgsw(self):
        # Deprecated.

        for i in range(0, 2):
            ip = self.net["autopg1"].usable[i]
            hostname = "utpgsw%d.aqd-unittest.ms.com" % i

            self.dsdb_expect_add(hostname, ip, "xge49",
                                 ip.mac)
            command = ["add", "switch", "--switch", hostname, "--rack", "ut12",
                       "--model", "rs g8000", "--interface", "xge49",
                       "--type", "tor", "--mac", ip.mac, "--ip", ip]
            self.ignoreoutputtest(command)
        self.dsdb_verify()

    # see     def testverifypollut01ga2s01(self):
    # see fakevlan2net
    def test_003_pollutpgsw(self):
        macs = ["02:02:04:02:12:05", "02:02:04:02:12:06"]
        for i in range(0, 2):
            command = ["poll", "switch", "--vlan", "--switch",
                       "utpgsw%d.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)

            service = self.config.get("broker", "poll_helper_service")
            self.matchoutput(err,
                             "Using jump host nyaqd1.ms.com from service "
                             "instance %s/unittest to run discovery "
                             "for switch utpgsw%d.aqd-unittest.ms.com" %
                             (service, i),
                             command)

            # For Nexus switches we have if names, not snmp ids.
            command = "show switch --switch utpgsw%d.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Port et1-1: %s" % macs[i], command)

    # for each cluster's hosts
    def test_004_add10gigracks(self):
        for i in range(0, 2):
            machine = "utpgs01p%d" % i
            self.create_machine(machine, "vb1205xm", rack="ut3",
                                eth0_mac=self.net["autopg2"].usable[i].mac)

    def test_006_populate10gigrackhosts(self):
        for i in range(0, 2):
            ip = self.net["autopg2"].usable[i]
            hostname = "utpgh%d.aqd-unittest.ms.com" % i
            machine = "utpgs01p%d" % i

            self.dsdb_expect_add(hostname, ip, "eth0", ip.mac)
            command = ["add", "host", "--hostname", hostname, "--ip", ip,
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan2-10g-test"]
            self.noouttest(command)
        self.dsdb_verify()

    def test_007_makeclusters(self):
        for i in range(0, 2):

            host = "utpgh%s.aqd-unittest.ms.com" % i
            cluster = "utpgcl%d" % i
            self.successtest(["make", "cluster", "--cluster", cluster])

            self.successtest(["cluster",
                              "--hostname", host, "--cluster", cluster])

    def test_008_addmachines(self):
        for i in range(0, 3):
            cluster = "utpgcl%d" % (i / 2)
            machine = "utpgm%d" % i

            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", cluster, "--model", "utmedium"])

    def test_009_addswitch(self):
        for i in range(0, 2):
            self.successtest(["update_esx_cluster", "--cluster=utpgcl%d" % i,
                              "--switch=utpgsw%d.aqd-unittest.ms.com" % i])

    def test_010_addstorageips(self):
        # storage IPs
        for i in range(0, 2):
            ip = self.net["vm_storage_net"].usable[i + 26]
            machine = "utpgs01p%d" % i

            self.noouttest(["add", "interface", "--interface", "eth1",
                            "--machine", machine,
                            "--mac", ip.mac])

            self.dsdb_expect_add("utpgh%d-eth1.aqd-unittest.ms.com" % i,
                                 ip, "eth1", ip.mac,
                                 primary="utpgh%d.aqd-unittest.ms.com" % i)
            command = ["add", "interface", "address", "--machine", machine,
                       "--interface", "eth1", "--ip", ip]
            self.noouttest(command)
        self.dsdb_verify()

    def test_011_catutpgcl0(self):
        data_command = ["cat", "--cluster", "utpgcl0", "--data"]
        data = self.commandtest(data_command)

        self.matchoutput(data, '"system/cluster/rack/room" = "utroom1";',
                         data_command)

        data_command = ["cat", "--machine", "utpgs01p0"]
        data = self.commandtest(data_command)

        self.matchoutput(data, '"rack/name" = "ut3";',
                         data_command)
        self.matchoutput(data, '"rack/room" = "utroom1";',
                         data_command)

    # Autopg test
    def test_100_addinterfaces(self):
        # These ones fit the 2 address net
        for i in range(0, 2):
            machine = "utpgm%d" % i
            self.noouttest(["add", "interface", "--machine", machine,
                            "--interface", "eth0", "--automac", "--autopg"])

        # The third one shall fail
        command = ["add", "interface", "--machine", "utpgm%d" % 2,
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on switch "
                         "utpgsw1.aqd-unittest.ms.com",
                         command)

    def test_101_verify_audit(self):
        command = ["search_audit", "--command", "add_interface",
                   "--keyword", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "pg=user-v710", command)

#    Storage group / resource tests
    def test_101_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--required_type=share"]
        self.successtest(command)

        command = ["show_resourcegroup", "--cluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Bound to: ESX Metacluster utmc8", command)

        command = ["add_resourcegroup", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--required_type=share"]
        self.successtest(command)

        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Resource Group: utmc8as2", command)

    def test_102_verify_metacluster(self):
        self.successtest(["make", "cluster", "--cluster", "utmc8"])

        command = ["cat", "--cluster", "utmc8", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template clusterdata/utmc8;", command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc8";', command)
        self.matchoutput(out, '"system/metacluster/type" = "meta";', command)
        self.searchoutput(out,
                          r'"system/metacluster/members" = list\(\s*'
                          r'"utpgcl0",\s*'
                          r'"utpgcl1"\s*'
                          r'\);',
                          command)
        self.matchoutput(out, '"system/build" = "build";', command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/location" = "ut.ny.na";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/continent" = "na";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/city" = "ny";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/campus" = "ny";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/building" = "ut";',
                         command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as1/config"));',
                         command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as2/config"));',
                         command)

    def test_103_add_share_to_rg(self):
        command = ["add_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)

        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["show_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as2", command)

    def test_104_add_same_share_name_fail(self):
        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--share=test_v2_share"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: Share test_v2_share, "
                         "bundleresource instance already exists.", command)

    def test_105_search_share(self):
        command = ["search_cluster", "--share", "test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def test_105_cat_rg(self):
        command = ["cat", "--resourcegroup=utmc8as1", "--cluster=utmc8",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/config;",
                         command)
        self.matchoutput(out, '"name" = "utmc8as1', command)
        self.matchoutput(out,
                         '"resources/share" = '
                         'append(create("resource/cluster/utmc8/resourcegroup/'
                         'utmc8as1/share/test_v2_share/config"));',
                         command)

        # TODO no resources, waiting for big resource branch

    def test_106_cat_share(self):
        command = ["cat", "--share=test_v2_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/share/test_v2_share/config;",
                         command)
        self.matchoutput(out, '"name" = "test_v2_share";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_v2_share";',
                         command)

    def test_107_cat_switch(self):
        for i in range(0, 2):
            command = ["cat", "--switch", "utpgsw%d" % i]

            out = self.commandtest(command)
            self.matchoutput(out, '"user-v710", nlist(', command)

    def test_108_addutpgmdisk(self):
        for i in range(0, 3):
            self.noouttest(["add", "disk", "--machine", "utpgm%d" % i,
                            "--disk", "sda", "--controller", "scsi",
                            "--snapshot", "--share", "test_v2_share",
                            "--size", "34", "--resourcegroup", "utmc8as1",
                            "--address", "0:0"])

    def test_109_verifyaddutpgm0disk(self):
        command = "show machine --machine utpgm0"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk from test_v2_share\) "
                          r"\[boot,snapshot\]$", command)

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
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

    def test_111_addfilesystemfail(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--resourcegroup=utmc8as1"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: Resource's filesystem type "
                         "differs from the requested share",
                         command)

    def test_112_verify_rg(self):
        command = ["show_resourcegroup", "--cluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_113_verifyutmc8(self):
        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_114_share(self):
        command = ["search_machine", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utpgm0", command)
        self.matchclean(out, "evm2", command)
        self.matchclean(out, "evm10", command)

    def test_115_search_host_by_metacluster(self):
        command = "search host --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgh0.aqd-unittest.ms.com", command)
        self.matchoutput(out, "utpgh1.aqd-unittest.ms.com", command)

    def test_116_search_machine_by_metacluster(self):
        command = "search machine --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgm0", command)
        self.matchoutput(out, "utpgm1", command)
        self.matchoutput(out, "utpgm2", command)
        self.matchclean(out, "utpgs01p0", command)

    def test_120_move_machine_pre(self):
        command = ["show_machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utpgcl0", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk from test_v2_share\) "
                          r"\[boot,snapshot\]$",
                          command)

    def test_121_move_machine(self):
        # Moving the machine from one cluster to the other exercises the case in
        # the disk movement logic when the old share is inside a resource group.
        command = ["update_machine", "--machine", "utpgm0",
                   "--cluster", "utpgcl1"]
        self.noouttest(command)

    def test_122_verify_move(self):
        command = ["show_machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utpgcl1", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk from test_v2_share\) "
                          r"\[boot,snapshot\]$",
                          command)

#    metacluster aligned svc tests
    def test_150_addvcenterservices(self):
        command = ["add", "service", "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

        command = ["add", "service", "--service", "vcenter", "--instance", "np"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-10g-test"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

    def test_151_mapvcenterservices(self):
        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut", "--personality", "vulcan2-10g-test",
                   "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "np",
                   "--building", "np", "--personality", "vulcan2-10g-test",
                   "--archetype", "vmhost"]
        self.noouttest(command)

    def test_152_bindvcenterservices(self):
        command = ["bind_cluster", "--cluster", "utmc8", "--service", "vcenter",
                   "--instance", "ut"]
        err = self.statustest(command)
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service vcenter instance ut", command)

        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host utpgh0.aqd-unittest.ms.com adding binding "
                         "for service vcenter instance ut", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Uses Service: vcenter Instance: ut",
                         command)

        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Member Alignment: Service vcenter Instance ut", command)

    def test_152_failmaxclientcount(self):
        command = ["update_service", "--service", "vcenter", "--instance", "ut",
                   "--max_clients", "17"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut"]
        self.noouttest(command)

        self.add_utcluster("utpgcl2", "utmc8")

        command = ["make", "cluster", "--cluster", "utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The available instances ['ut'] for service vcenter "
                         "are at full capacity.",
                         command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut"]
        self.noouttest(command)

        command = ["del_esx_cluster", "--cluster=utpgcl2"]
        self.successtest(command)

    def test_153_unbindvcenterservices(self):
        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-10g-test"]
        self.noouttest(command)

        command = ["unbind_cluster", "--cluster", "utmc8",
                   "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

    def test_154_unmapvcenterservices(self):
        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut",
                   "--personality", "vulcan2-10g-test", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "np", "--building", "np",
                   "--personality", "vulcan2-10g-test", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host utpgh0.aqd-unittest.ms.com removing "
                         "binding for service vcenter instance ut", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out,
                        "Uses Service: vcenter Instance: ut",
                        command)

    def test_155_delvcenterservices(self):
        command = ["del", "service", "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

        command = ["del", "service", "--service", "vcenter", "--instance", "np"]
        self.noouttest(command)

#
##    service binding conflicts
#
    def test_170_add_mc_esx_service(self):
        command = ["add", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["bind_cluster", "--cluster", "utmc8", "--service", "esx_management_server",
                   "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service esx_management_server instance ut.mc", command)

    def test_170_fail_make_host(self):
        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Replacing ut.a instance with ut.mc (bound to "
                         "ESX metacluster utmc8) for service esx_management_server",
                         command)
        self.matchoutput(out,
                         "ESX Cluster utpgcl0 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for utpgh0.aqd-unittest.ms.com.",
                         command)

    def test_175_verify_client_count(self):
        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 16$", command)

    def test_175_verify_mixed_client_count(self):
        self.add_utcluster("utpgcl3", "utmc8")
        command = ["bind_cluster", "--cluster", "utpgcl3", "--service",
                   "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "ESX Cluster utpgcl3 adding binding for service "
                         "esx_management_server instance ut.mc", command)

        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 24$", command)

        # Can't unbind an an aligned service here and don't want unalign it

        command = ["del_esx_cluster", "--cluster=utpgcl3"]
        self.successtest(command)

    def test_180_remove_mc_esx_service(self):
        command = ["del_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["unbind_cluster", "--cluster", "utmc8", "--service", "esx_management_server",
                   "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["del", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

#    Storage group related deletes

    def test_202_delutpgmdisk(self):
        for i in range(0, 3):
            self.noouttest(["del", "disk", "--machine", "utpgm%d" % i,
                            "--controller", "scsi", "--disk", "sda"])

    def test_204_delresourcegroup(self):
        command = ["del_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8"]
        self.successtest(command)

        command = ["del_share", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8"]
        self.successtest(command)

    # Metacluster / cluster / Switch deletes
    def test_305_delinterfaces(self):
        for i in range(0, 2):
            ip = self.net["vm_storage_net"].usable[i + 26]
            machine = "utpgs01p%d" % i

            self.dsdb_expect_delete(ip)
            command = ["del", "interface", "address", "--machine", machine,
                       "--interface", "eth1", "--ip", ip]
            self.noouttest(command)

            self.noouttest(["del", "interface", "--interface", "eth1",
                            "--machine", machine])
        self.dsdb_verify()

    def test_306_delmachines(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            self.noouttest(["del", "machine", "--machine", machine])

    def test_307_del10gigrackhosts(self):
        for i in range(0, 2):
            basetime = datetime.now()
            ip = self.net["autopg2"].usable[i]
            hostname = "utpgh%d.aqd-unittest.ms.com" % i

            self.dsdb_expect_delete(ip)
            command = ["del", "host", "--hostname", hostname]
            self.successtest(command)
            self.wait_notification(basetime, 1)
        self.dsdb_verify()

    def test_307_del10gigracks(self):
        for port in range(0, 2):
            self.noouttest(["del", "machine", "--machine",
                            "utpgs01p%d" % port])

    def test_308_delutpgsw(self):
        for i in range(0, 2):
            ip = self.net["autopg1"].usable[i]
            swname = "utpgsw%d.aqd-unittest.ms.com" % i
            plenary = self.plenary_name("switchdata", swname)
            self.failUnless(os.path.exists(plenary),
                            "Plenary file '%s' does not exist" % plenary)

            self.dsdb_expect_delete(ip)
            command = "del switch --switch %s" % swname
            self.noouttest(command.split(" "))

            self.failIf(os.path.exists(plenary),
                        "Plenary file '%s' still exists" % plenary)

        self.dsdb_verify()

    def test_309_delutpgcl(self):
        command = ["del_metacluster", "--metacluster=utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "ESX Metacluster utmc8 is still in use by "
                         "clusters: utpgcl0, utpgcl1.", command)

        for i in range(0, 2):
            command = ["del_esx_cluster", "--cluster=utpgcl%d" % i]
            self.successtest(command)

    def test_310_delutmc8(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc8"]
        err = self.statustest(command)
        self.wait_notification(basetime, 1)

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utmc8%s" % self.profile_suffix)))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcan20)
    unittest.TextTestRunner(verbosity=2).run(suite)
