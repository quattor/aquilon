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
