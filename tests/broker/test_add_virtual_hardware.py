#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing commands that add virtual hardware."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddVirtualHardware(TestBrokerCommand):

    def test_100_add_utecl1_machines(self):
        for i in range(1, 9):
            self.noouttest(["add", "machine", "--machine", "evm%s" % i,
                            "--cluster", "utecl1", "--model", "utmedium"])

    def test_101_add_next_machine(self):
        command = ["add", "machine", "--prefix", "evm",
                   "--cluster", "utecl2", "--model", "utmedium"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm9", command)

    def test_102_verify_audit(self):
        command = ["search_audit", "--command", "add_machine", "--limit", 1,
                   "--keyword", "evm", "--argument", "prefix"]
        out = self.commandtest(command)
        self.matchoutput(out, "[Result: machine=evm9]", command)

    def test_102_verify_audit_argument(self):
        command = ["search_audit", "--command", "add_machine",
                   "--keyword", "evm9", "--argument", "__RESULT__:machine"]
        out = self.commandtest(command)
        self.matchoutput(out, "[Result: machine=evm9]", command)
        command = ["search_audit", "--keyword", "evm9", "--argument", "machine"]
        self.noouttest(command)

    def test_105_verify_machine_count(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Virtual Machine count: 8", command)

        command = ["show_esx_cluster", "--cluster=utecl2"]
        out = self.commandtest(command)
        self.matchoutput(out, "ESX Cluster: utecl2", command)
        self.matchoutput(out, "Virtual Machine count: 1", command)

    def test_105_make_utecl1(self):
        # This should succeed, silently skipping all VMs (no interfaces or
        # disks).
        command = ["make_cluster", "--cluster=utecl1"]
        (out, err) = self.successtest(command)

    def test_110_add_interfaces_automac(self):
        for i in range(1, 8):
            self.noouttest(["add", "interface", "--machine", "evm%s" % i,
                            "--interface", "eth0", "--automac"])

    def test_111_add_evm9_interface(self):
        self.noouttest(["add", "interface", "--machine", "evm9",
                        "--interface", "eth0", "--mac", "00:50:56:3f:ff:ff"])

    def test_112_add_interface_automac_hole(self):
        # This should now fill in the 'hole' between 7 and 9
        self.noouttest(["add", "interface", "--machine", "evm8",
                        "--interface", "eth0", "--automac"])

    def test_113_verifyaudit(self):
        for i in range(1, 9):
            command = ["search", "audit", "--command", "add_interface",
                       "--keyword", "evm%d" % i]
            out = self.commandtest(command)
            self.matchoutput(out,
                             "[Result: mac=00:50:56:01:20:%02x]" % (i - 1),
                             command)

    def test_119_makecluster(self):
        # This should succeed, silently skipping all VMs (no disks).
        command = ["make_cluster", "--cluster=utecl1"]
        self.successtest(command)

    def test_120_adddisks(self):
        # The first 8 shares should work...
        for i in range(1, 9):
            self.noouttest(["add", "disk", "--machine", "evm%s" % i,
                            "--disk", "sda", "--controller", "sata",
                            "--size", "15", "--share", "test_share_%s" % i,
                            "--address", "0:0"])

    def test_125_searchhostmemberclustershare(self):
        command = ["search_host", "--member_cluster_share=test_share_1"]
        out = self.commandtest(command)
        for i in range(2, 5):
            self.matchoutput(out, "evh%s.aqd-unittest.ms.com" % i, command)
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)

    def test_125_verifydiskcount(self):
        command = ["show_share", "--cluster=utecl1", "--share=test_share_1"]
        out = self.commandtest(command)

        self.matchoutput(out, "Share: test_share_1", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 1", command)
        self.matchoutput(out, "Machine Count: 1", command)

    def test_125_verify_metacluster_shares(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "MetaCluster: utmc1", command)
        for i in range(1, 9):
            self.matchoutput(out, "Share: test_share_%s" % i, command)
        self.matchclean(out, "test_share_9", command)

    def test_129_make_utecl1(self):
        # Now with disks
        command = ["make_cluster", "--cluster=utecl1"]
        self.successtest(command)

    def test_130_show_utecl1_machines(self):
        # Skipping evm9 since the mac is out of sequence and different cluster
        for i in range(1, 9):
            command = "show machine --machine evm%s" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Machine: evm%s" % i, command)
            self.matchoutput(out, "Model Type: virtual_machine", command)
            self.matchoutput(out, "Hosted by: ESX Cluster utecl1", command)
            self.matchoutput(out, "Building: ut", command)
            self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)
            self.matchoutput(out, "Cpu: xeon_5150 x 1", command)
            self.matchoutput(out, "Memory: 8192 MB", command)
            self.searchoutput(out,
                              r"Interface: eth0 00:50:56:01:20:%02x \[boot, default_route\]"
                              r"\s+Type: public"
                              r"\s+Vendor: utvirt Model: default" %
                              (i - 1),
                              command)
            self.searchoutput(out,
                              r'Disk: sda 15 GB sata \(virtual_disk stored on share test_share_%d\) \[boot\]\s*'
                              r'Address: 0:0$' % i,
                              command)

    def test_130_cat_utecl1_tmachines(self):
        # Skipping evm9 since the mac is out of sequence
        for i in range(1, 9):
            command = "cat --machine evm%s" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"location" = "ut.ny.na";', command)
            self.matchoutput(out,
                             'include { "hardware/machine/utvendor/utmedium" };',
                             command)
            self.searchoutput(out,
                              r'"ram" = list\(\s*'
                              r'create\("hardware/ram/generic",\s*'
                              r'"size", 8192\*MB\s*\)\s*\);',
                              command)
            self.searchoutput(out,
                              r'"cpu" = list\(\s*'
                              r'create\("hardware/cpu/intel/xeon_5150"\)\s*\);',
                              command)
            self.searchoutput(out,
                              r'"cards/nic/eth0" = '
                              r'create\("hardware/nic/utvirt/default",\s*'
                              r'"boot", true,\s*'
                              r'"hwaddr", "00:50:56:01:20:%02x"\s*\);'
                              % (i - 1),
                              command)
            self.searchoutput(out,
                              r'"harddisks/\{sda\}" = nlist\(\s*'
                              r'"address", "0:0",\s*'
                              r'"boot", true,\s*'
                              r'"capacity", 15\*GB,\s*'
                              r'"interface", "sata",\s*'
                              r'"mountpoint", "/vol/lnn30f1v1/test_share_%d",\s*'
                              r'"path", "evm%d/sda.vmdk",\s*'
                              r'"server", "lnn30f1",\s*'
                              r'"sharename", "test_share_%d"\s*'
                              r'\);' % (i, i, i),
                              command)

    def test_130_cat_utecl1(self):
        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template clusterdata/utecl1;", command)
        self.matchoutput(out, '"system/cluster/name" = "utecl1";', command)
        self.matchoutput(out, '"system/cluster/metacluster/name" = "utmc1";', command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc1";', command)
        self.matchoutput(out, '"system/cluster/max_hosts" = 8;', command)
        self.matchoutput(out, '"system/cluster/down_hosts_threshold" = 2;',
                         command)
        self.matchclean(out, "hostname", command)
        for i in range(1, 9):
            machine = "evm%s" % i
            self.searchoutput(out,
                              r'"system/resources/virtual_machine" = '
                              r'append\(create\("resource/cluster/utecl1/virtual_machine/%s/config"\)\);'
                              % machine,
                              command)
        self.matchclean(out, "evm9", command)

        command = "cat --cluster=utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template clusters/utecl1;", command)
        self.searchoutput(out,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          command)

    def test_130_cat_utecl1_resources(self):
        for i in range(1, 9):
            machine = "evm%s" % i
            command = ["cat", "--cluster", "utecl1",
                       "--virtual_machine", machine]
            out = self.commandtest(command)
            self.searchoutput(out,
                              r'"hardware" = create\("machine/americas/ut/None/%s"\);' %
                              machine,
                              command)
            self.matchclean(out, "system", command)

    def test_130_show_utecl1(self):
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 8", command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Virtual Machine count: 8", command)
        self.matchoutput(out, "ESX VMHost count: 3", command)
        self.matchoutput(out, "Personality: vulcan-10g-server-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        for i in range(1, 9):
            machine = "evm%s" % i
            self.matchoutput(out, "Virtual Machine: %s (no hostname, 8192 MB)" %
                             machine, command)

    def test_140_add_windows(self):
        command = ["add_windows_host", "--hostname=aqddesk1.msad.ms.com",
                   "--osversion=nt61e",
                   "--machine=evm1", "--comments=Windows Virtual Desktop"]
        self.noouttest(command)

    def test_145_verify_windows_vm(self):
        command = ["cat", "--cluster", "utecl1", "--virtual_machine", "evm1"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"build", "build",', command)
        self.matchoutput(out, '"name", "windows"', command)
        self.matchoutput(out, '"os", "windows"', command)
        self.matchoutput(out, '"osversion", "nt61e"', command)
        self.matchoutput(out, '"hostname", "aqddesk1"', command)
        self.matchoutput(out, '"domainname", "msad.ms.com"', command)

    def test_145_verify_windows(self):
        command = "show host --hostname aqddesk1.msad.ms.com"

        out = self.commandtest(command.split(" "))

        self.searchoutput(out, r"^Machine: evm1", command)
        self.searchoutput(out, r"^    Model Type: virtual_machine", command)
        self.searchoutput(out, r"^  Primary Name: aqddesk1.msad.ms.com",
                          command)
        self.searchoutput(out, r"^  Host Comments: Windows Virtual Desktop", command)
        self.searchoutput(out,
                          r'Operating System: windows\s*'
                          r'Version: nt61e$',
                          command)
        self.searchoutput(out, r"^    Comments: Windows 7 Enterprise \(x86\)",
                          command)

    def test_149_makecluster(self):
        # Now with Windows VM
        command = ["make_cluster", "--cluster=utecl1"]
        self.successtest(command)

    def test_200_add_utmc4_machines(self):
        for i in range(0, 18):
            cluster = "utecl%d" % (5 + (i // 3))
            machine = "evm%d" % (10 + i)
            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", cluster, "--model", "utmedium"])

    def test_201_search_network_fail(self):
        command = ["search_network", "--machine=evm18"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine evm18 has no interfaces with a port group "
                         "or assigned to a network.",
                         command)

    def test_210_add_utmc4_interfaces(self):
        # Skip index 8 and 17 - these will fail.
        for i in range(0, 8) + range(9, 17):
            machine = "evm%d" % (10 + i)
            self.noouttest(["add", "interface", "--machine", machine,
                            "--interface", "eth0", "--automac", "--autopg"])

    def test_211_evm18_no_pg(self):
        command = ["add", "interface", "--machine", "evm18",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on switch "
                         "ut01ga2s01.aqd-unittest.ms.com",
                         command)

    def test_212_evm27_no_pg(self):
        command = ["add", "interface", "--machine", "evm27",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on switch "
                         "ut01ga2s02.aqd-unittest.ms.com",
                         command)

    # We are checking the portgroups the machines have been mapped to
    # evm10 -> user-v710, evm11 -> user-v711, evm12 -> user-v712, evm13 -> user-v13
    # evm14 -> user-v710, evm15 -> user-v711, evm16 -> user-v712, evm17 -> user-v13
    # and so on and so forth
    def test_215_verify_search_machine_pg(self):
        for i in range(0, 8) + range(9, 17):
            if i < 9:
                port_group = "user-v71%d" % (i % 4)
            else:
                port_group = "user-v71%d" % ((i - 9) % 4)
            machine = "evm%d" % (i + 10)
            command = ["search_machine", "--machine", machine,
                       "--pg", port_group]
            out = self.commandtest(command)
            self.matchoutput(out, machine, command)

    def test_215_verify_search_network_machine(self):
        command = ["search_network", "--machine=evm10"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["ut01ga2s01_v710"]), command)

    # Utility method...
    def verifypg(self):
        command = ["search_machine", "--machine=evm10", "--pg=user-v710"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm10", command)

    # These set of port group tests needs to happen before the hosts are added,
    # because otherwise the primary name of the host would be inculded in the
    # number of existing allocations, and that would prevent re-adding the
    # interface to the port group.
    def test_220_updatenoop(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", "user-v710"]
        self.noouttest(command)
        self.verifypg()

    def test_221_show_evm10_proto(self):
        command = ["show_machine", "--machine", "evm10", "--format", "proto"]
        machine = self.protobuftest(command, expect=1)[0]
        self.assertEqual(machine.interfaces[0].port_group_tag, 710)
        self.assertEqual(machine.interfaces[0].port_group_usage, "user")
        self.assertEqual(machine.interfaces[0].port_group_name, "user-v710")

    def test_222_updateclear(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", ""]
        self.noouttest(command)
        command = ["show_machine", "--machine=evm10"]
        out = self.commandtest(command)
        self.matchclean(out, "Port Group", command)

    def test_223_updatemanual(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", "user-v710"]
        self.noouttest(command)
        self.verifypg()

    def test_224_updateauto(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", ""]
        self.noouttest(command)
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--autopg"]
        self.noouttest(command)
        self.verifypg()

    def test_230_add_utmc4_disks(self):
        for i in range(0, 18):
            share = "utecl%d_share" % (5 + (i // 3))
            machine = "evm%d" % (10 + i)
            self.noouttest(["add", "disk", "--machine", machine,
                            "--disk", "sda", "--controller", "sata",
                            "--size", "15", "--share", share,
                            "--address", "0:0"])

    def test_240_add_utmc4_aux(self):
        net = self.net["vm_storage_net"]
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                port = i
                machine = "ut11s01p%d" % port
            else:
                port = i - 12
                machine = "ut12s02p%d" % port
            self.dsdb_expect_add(hostname, net.usable[i - 1],
                                 "eth1", net.usable[i - 1].mac,
                                 "evh%d.aqd-unittest.ms.com" % (i + 50))
            command = ["add_interface_address", "--fqdn", hostname,
                       "--machine", machine, "--interface", "eth1", "--autoip"]
            self.noouttest(command)
        self.dsdb_verify()

    def test_245_verify_utmc4_aux(self):
        command = ["show", "network", "--hosts",
                   "--ip", self.net["vm_storage_net"].ip]
        out = self.commandtest(command)
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            self.matchoutput(out, hostname, command)

    def test_250_delmachines(self):
        # Need to remove machines without interfaces or the make will fail.
        self.noouttest(["del", "machine", "--machine", "evm18"])
        self.noouttest(["del", "machine", "--machine", "evm27"])

    def test_255_makecluster(self):
        for i in range(5, 11):
            command = ["make_cluster", "--cluster=utecl%s" % i]
            self.successtest(command)

    def test_260_verifycatmachines(self):
        for i in range(0, 8):
            command = "cat --machine evm%s" % (10 + i)
            port_group = "user-v71%d" % (i % 4)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, """"location" = "ut.ny.na";""", command)
            self.matchoutput(out,
                             'include { "hardware/machine/utvendor/utmedium" };',
                             command)
            self.searchoutput(out,
                              r'"ram" = list\(\s*'
                              r'create\("hardware/ram/generic",\s*'
                              r'"size", 8192\*MB\s*\)\s*\);',
                              command)
            self.searchoutput(out,
                              r'"cpu" = list\(\s*'
                              r'create\("hardware/cpu/intel/xeon_5150"\)\s*\);',
                              command)
            self.searchoutput(out,
                              r'"cards/nic/eth0" = '
                              r'create\("hardware/nic/utvirt/default",\s*'
                              r'"boot", true,\s*'
                              r'"hwaddr", "00:50:56:[0-9a-f:]{8}",\s*'
                              r'"port_group", "%s"\s*\);'
                              % port_group,
                              command)

    # Because the machines are allocated across portgroups, the IP addresses
    # allocated by autoip also differ
    # evm10 -> self.net["ut01ga2s01_v710"].usable[0]
    # evm11 -> self.net["ut01ga2s01_v711"].usable[0]
    # evm12 -> self.net["ut01ga2s01_v712"].usable[0]
    # evm13 -> self.net["ut01ga2s01_v713"].usable[0]
    # evm14 -> self.net["ut01ga2s01_v710"].usable[1]
    # As each subnet only has two usable IPs, when we get to evm19 it becomes
    # evm19 -> self.net["ut01ga2s02_v710"].usable[0]
    # and the above pattern repeats
    def test_270_add_hosts(self):
        # Skip index 8 and 17 - these don't have interfaces. Index 16 will be
        # used for --prefix testing.
        mac_prefix = "00:50:56:01:20"
        mac_idx = 8
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        for i in range(0, 8) + range(9, 16):
            machine = "evm%d" % (10 + i)
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)

            if i < 9:
                net_index = (i % 4)
                usable_index = i // 4
            else:
                net_index = ((i - 9) % 4) + 4
                usable_index = (i - 9) // 4
            ip = nets[net_index].usable[usable_index]

            # FIXME: the MAC check is fragile...
            self.dsdb_expect_add(hostname, ip, "eth0",
                                 "%s:%02x" % (mac_prefix, mac_idx))
            mac_idx += 1

            command = ["add_host", "--hostname", hostname,
                       "--machine", machine, "--autoip", "--domain=unittest",
                       "--archetype=aquilon", "--personality=inventory"]
            (out, err) = self.successtest(command)
        self.dsdb_verify()

    def test_271_add_host_prefix(self):
        ip = self.net["ut01ga2s02_v713"].usable[1]
        mac = "00:50:56:01:20:17"
        self.dsdb_expect_add("ivirt17.aqd-unittest.ms.com", ip, "eth0", mac)
        command = ["add", "host", "--prefix", "ivirt", "--machine", "evm26",
                   "--autoip", "--domain", "unittest",
                   "--archetype", "aquilon", "--personality", "inventory"]
        out = self.commandtest(command)
        # This also verifies that we use the mapping for the building, not the
        # city
        self.matchoutput(out, "ivirt17.aqd-unittest.ms.com", command)
        self.dsdb_verify()

    def test_275_verify_add_host(self):
        # This test also verifies the --autoip allocation logic
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        for i in range(0, 8) + range(9, 17):
            if i < 9:
                net_index = (i % 4)
                usable_index = i // 4
            else:
                net_index = ((i - 9) % 4) + 4
                usable_index = (i - 9) // 4
            hostname = "ivirt%d.aqd-unittest.ms.com" % (i + 1)
            ip = nets[net_index].usable[usable_index]
            command = "search host --hostname %s --ip %s" % (hostname, ip)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, hostname, command)

    def test_276_verify_audit(self):
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        i = 16
        net_index = ((i - 9) % 4) + 4
        usable_index = (i - 9) // 4
        ip = nets[net_index].usable[usable_index]
        command = ["search", "audit", "--keyword",
                   "ivirt%d.aqd-unittest.ms.com" % (i + 1)]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "[Result: hostname=ivirt%d.aqd-unittest.ms.com "
                         "ip=%s]" % (i + 1, ip),
                         command)

    def test_280_make_hosts(self):
        for i in range(0, 8) + range(9, 17):
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)
            command = ["make", "--hostname", hostname]
            (out, err) = self.successtest(command)

    # Drop evm26 for appliance reuse
    def test_290_del_ivirt17(self):
        ip = self.net["ut01ga2s02_v713"].usable[1]
        command = ["del_host", "--hostname", "ivirt17.aqd-unittest.ms.com"]

        self.dsdb_expect_delete(ip)
        self.statustest(command)
        self.dsdb_verify()

    def test_291_del_evm26(self):
        machine = "evm26"
        self.noouttest(["del_machine", "--machine", machine])

    # FIXME: we need a more generic test to check if a host/cluster may contain
    # VMs. Perhaps an attribute of Archetype or Personality?
    # def testfailaddnonvirtualcluster(self):
    #     command = ["add", "machine", "--machine", "ut9s03p51",
    #                "--cluster", "utgrid1", "--model", "utmedium"]
    #     out = self.badrequesttest(command)
    #     self.matchoutput(out,
    #                      "Can only add virtual machines to "
    #                      "clusters with archetype esx_cluster.",
    #                      command)

    # The current client does not allow this test.
#   def test_900_failbadlocation(self):
#       command = ["add_machine", "--machine=evm999", "--rack=np997",
#                  "--model=utmedium", "--cluster=utecl1"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out,
#                        "Cannot override cluster location building ut "
#                        "with location rack np997",
#                        command)

    # Replacement for the test above.
    def test_900_bad_location(self):
        command = ["add_machine", "--machine=evm999", "--rack=np997",
                   "--model=utmedium", "--cluster=utecl1"]
        out = self.badoptiontest(command)
        self.matchoutput(out,
                         "Please provide exactly one of the required options!",
                         command)

    def test_900_bad_disk_address(self):
        command = ["add", "disk", "--machine", "evm8", "--disk", "sdc",
                   "--controller", "sata", "--size", "15",
                   "--share", "test_share_8", "--address", "badaddress"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Disk address 'badaddress' is not valid", command)

    def test_900_missing_cluster(self):
        command = ["add_machine", "--machine=ut9s03p51",
                   "--cluster=cluster-does-not-exist", "--model=utmedium"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

    def test_900_no_container(self):
        command = ["add_machine", "--machine=ut3c1n1", "--model=utmedium",
                   "--chassis=ut3c1.aqd-unittest.ms.com", "--slot=1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Virtual machines must be assigned to a cluster "
                         "or a host.",
                         command)

    def test_900_nonvirtual(self):
        command = ["add_machine", "--machine=ut3c1n1", "--cluster=utecl1",
                   "--model=hs21-8853"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model ibm/hs21-8853 is not a virtual machine.",
                         command)

    def test_900_pg_no_switch(self):
        command = ["add", "interface", "--machine", "evm1",
                   "--interface", "eth1", "--pg", "unused-v999"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl1 does not have either a virtual "
                         "switch or a network device assigned, automatic IP "
                         "address and port group allocation is not possible.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
