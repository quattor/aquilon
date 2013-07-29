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
"""Module for testing commands that add virtual hardware."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddVirtualHardware(TestBrokerCommand):

    def test_000_addmachines(self):
        for i in range(1, 9):
            self.noouttest(["add", "machine", "--machine", "evm%s" % i,
                            "--cluster", "utecl1", "--model", "utmedium"])

    def test_001_addnextmachine(self):
        command = ["add", "machine", "--prefix", "evm",
                   "--cluster", "utecl1", "--model", "utmedium"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm9", command)

    def test_002_verify_audit(self):
        command = ["search_audit", "--command", "add_machine", "--limit", 1,
                   "--keyword", "evm", "--argument", "prefix"]
        out = self.commandtest(command)
        self.matchoutput(out, "[Result: machine=evm9]", command)

    def test_002_verify_audit_argument(self):
        command = ["search_audit", "--command", "add_machine",
                   "--keyword", "evm9", "--argument", "__RESULT__:machine"]
        out = self.commandtest(command)
        self.matchoutput(out, "[Result: machine=evm9]", command)
        command = ["search_audit", "--keyword", "evm9", "--argument", "machine"]
        self.noouttest(command)

    def test_005_showmachinenorack(self):
        # The only way to test show machine with a machine that's not in
        # a rack is to use virtual hardware...
        command = ["show_machine", "--machine=evm1", "--format=csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm1,,ut,utvendor,utmedium,", command)

    def test_006_searchmachinenorack(self):
        # Ditto.
        command = ["search_machine", "--machine=evm1", "--format=csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm1,,ut,utvendor,utmedium,", command)

    def test_010_failwithoutcluster(self):
        command = ["add_machine", "--machine=evm999", "--rack=ut3",
                   "--model=utmedium"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Virtual machines must be assigned to a cluster "
                         "or a host.",
                         command)

    # The current client does not allow this test.
#   def test_010_failbadlocation(self):
#       command = ["add_machine", "--machine=evm999", "--rack=np997",
#                  "--model=utmedium", "--cluster=utecl1"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out,
#                        "Cannot override cluster location building ut "
#                        "with location rack np997",
#                        command)

    # Replacement for the test above.
    def test_010_failbadlocation(self):
        command = ["add_machine", "--machine=evm999", "--rack=np997",
                   "--model=utmedium", "--cluster=utecl1"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "cluster conflicts with rack", command)

    def test_050_addutmc5machines(self):
        # 2 clusters, 12 vmhosts with 24G RAM each, down_hosts_threshold=2
        # All machines should fit inside one cluster
        for i in range(0, 13):
            machine = "evm%d" % (i + 50)
            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", "utecl11", "--model", "utmedium"])
            machine = "evm%d" % (i + 70)
            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", "npecl11", "--model", "utmedium"])

    def test_051_addutmc6machines(self):
        # 2 clusters, 12 vmhosts with 24G RAM each, down_hosts_threshold=2
        # The machines should not fit inside one cluster
        for i in range(0, 15):
            machine = "evm%d" % (i + 90)
            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", "utecl12", "--model", "utmedium",
                            "--memory", 16384])
            machine = "evm%d" % (i + 110)
            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", "npecl12", "--model", "utmedium",
                            "--memory", 16384])

    def test_052_verify_capacity(self):
        # Verify that we could fill the cluster completely
        command = ["show", "esx", "cluster", "--cluster", "npecl12"]
        out = self.commandtest(command)
        self.matchoutput(out, "Capacity limits: memory: 245760", command)
        self.matchoutput(out, "Resources used by VMs: memory: 245760", command)

    def test_053_overcapacity(self):
        command = ["add", "machine", "--machine", "evm105", "--cluster",
                   "npecl12", "--model", "utmedium", "--memory", 16384]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster npecl12 is over capacity regarding memory",
                         command)

    def test_054_make_room(self):
        # Later tests need some room, so kill a few VMs
        for i in range(13, 15):
            self.noouttest(["del", "machine", "--machine", "evm%d" % (i + 90)])
            self.noouttest(["del", "machine", "--machine", "evm%d" % (i + 110)])

    def test_090_verifyaddmachines(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Virtual Machine count: 9", command)

    def test_095_makecluster(self):
        # This should succeed, silently skipping all VMs (no interfaces or
        # disks).
        command = ["make_cluster", "--cluster=utecl1"]
        (out, err) = self.successtest(command)

    # Resource definitions are generated even if the VM definition is incomplete
    #def test_096_clusterplenary(self):
    #    # The cluster plenary should not have VMs.
    #    command = ["cat", "--cluster=utecl1", "--data"]
    #    out = self.commandtest(command)
    #    self.matchclean(out, "resources/virtual_machine", command)

    def test_100_addinterfaces(self):
        for i in range(1, 8):
            self.noouttest(["add", "interface", "--machine", "evm%s" % i,
                            "--interface", "eth0", "--automac"])

    def test_110_addinterfaces(self):
        self.noouttest(["add", "interface", "--machine", "evm9",
                        "--interface", "eth0", "--mac", "00:50:56:3f:ff:ff"])

    def test_120_addinterfaces(self):
        # This should now fill in the 'hole' between 7 and 9
        self.noouttest(["add", "interface", "--machine", "evm8",
                        "--interface", "eth0", "--automac"])

    def test_125_addutmc5utmc6interfaces(self):
        for i in range(50, 63) + range(70, 83) + range(90, 103) + range(110, 123):
            machine = "evm%d" % i
            self.noouttest(["add_interface", "--machine", machine,
                            "--interface", "eth0", "--automac"])

    def test_126_makecluster(self):
        # This should succeed, silently skipping all VMs (no disks).
        command = ["make_cluster", "--cluster=utecl1"]
        (out, err) = self.successtest(command)

    # Resource definitions are generated even if the VM definition is incomplete
    #def test_127_clusterplenary(self):
    #    # The cluster plenary should not have VMs.
    #    command = ["cat", "--cluster=utecl1", "--data"]
    #    out = self.commandtest(command)
    #    self.matchclean(out, "resources/virtual_machine", command)

    def test_130_adddisks(self):
        # The first 8 shares should work...
        for i in range(1, 9):
            self.noouttest(["add", "disk", "--machine", "evm%s" % i,
                            "--disk", "sda", "--controller", "sata",
                            "--size", "15", "--share", "test_share_%s" % i,
                            "--address", "0:0"])

    def test_140_searchhostmemberclustershare(self):
        command = ["search_host", "--member_cluster_share=test_share_1"]
        out = self.commandtest(command)
        for i in range(2, 5):
            self.matchoutput(out, "evh%s.aqd-unittest.ms.com" % i, command)
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)

    def test_150_failaddillegaldisk(self):
        command = ["add", "disk", "--machine", "evm9", "--disk", "sda",
                   "--controller", "sata", "--size", "15",
                   "--share", "test_share_8", "--address", "badaddress"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Disk address 'badaddress' is not valid", command)

    def test_180_verifydiskcount(self):
        command = ["show_share", "--cluster=utecl1", "--share=test_share_1"]
        out = self.commandtest(command)

        self.matchoutput(out, "Share: test_share_1", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 1", command)
        self.matchoutput(out, "Machine Count: 1", command)

    def test_190_verifyadddisk(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "MetaCluster: utmc1", command)
        for i in range(1, 9):
            self.matchoutput(out, "Share: test_share_%s" % i, command)
        self.matchclean(out, "Share: test_share_9", command)

    def test_200_updatemachine(self):
        self.noouttest(["update_machine", "--machine", "evm9",
                        "--cluster", "utecl2"])
        oldpath = self.plenary_name("machine", "americas", "ut", "ut10", "evm9")
        newpath = self.plenary_name("machine", "americas", "ut", "None", "evm9")
        self.failIf(os.path.exists(oldpath),
                    "Plenary file '%s' not removed." % oldpath)
        self.failUnless(os.path.exists(newpath),
                        "Plenary file '%s' not created." % newpath)

    def test_300_failrebindhost(self):
        command = ["cluster", "--cluster=utecl1",
                   "--host=evh1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot support VMs", command)

    def test_310_failrebindmachine(self):
        command = ["update_machine", "--machine", "evm1",
                   "--cluster", "utecl2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "violates ratio", command)

    def test_500_verifyaddmachines(self):
        # Skipping evm9 since the mac is out of sequence and different cluster
        for i in range(1, 9):
            command = "show machine --machine evm%s" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Virtual_machine: evm%s" % i, command)
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

    def test_500_verifycatmachines(self):
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
                              r'"cards/nic" = nlist\(\s*'
                              r'"eth0", create\("hardware/nic/utvirt/default",\s*'
                              r'"boot", true,\s*'
                              r'"hwaddr", "00:50:56:01:20:%02x"\s*\)\s*\);'
                              % (i - 1),
                              command)

    def test_500_verifyaudit(self):
        for i in range(1, 9):
            command = ["search", "audit", "--command", "add_interface",
                       "--keyword", "evm%d" % i]
            out = self.commandtest(command)
            self.matchoutput(out,
                             "[Result: mac=00:50:56:01:20:%02x]" % (i - 1),
                             command)

    def test_500_verifycatcluster(self):
        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template clusterdata/utecl1;", command)
        self.matchoutput(out, '"system/cluster/name" = "utecl1";', command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc1";', command)
        self.searchoutput(out, '"system/cluster/ratio" = list\(\s*16,\s*1\s*\);',
                          command)
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

    def test_500_verifycatresource(self):
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

    def test_500_verifyshow(self):
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 8", command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Max vm_to_host_ratio: 16:1", command)
        self.matchoutput(out, "Max virtual machine count: 16", command)
        self.matchoutput(out, "Current vm_to_host_ratio: 8:3", command)
        self.matchoutput(out, "Virtual Machine count: 8", command)
        self.matchoutput(out, "ESX VMHost count: 3", command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        for i in range(1, 9):
            machine = "evm%s" % i
            self.matchoutput(out, "Virtual Machine: %s (no hostname, 8192 MB)" %
                             machine, command)

    def test_550_updatemachine(self):
        command = ["update_machine", "--machine=evm1", "--model=utlarge",
                   "--cpucount=2", "--memory=12288"]
        self.noouttest(command)

    def test_551_verifycatupdate(self):
        command = "cat --machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/utvendor/utlarge" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 12288\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_5150"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_5150"\)\s*\);',
                          command)
        # Updating the model of the machine changes the NIC model from
        # utvirt/default to generic/generic_nic
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "00:50:56:01:20:00"\s*\)\s*\);',
                          command)

    def test_552_verifyshowupdate(self):
        command = "show machine --machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Virtual_machine: evm1", command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Vendor: utvendor Model: utlarge", command)
        self.matchoutput(out, "Cpu: xeon_5150 x 2", command)
        self.matchoutput(out, "Memory: 12288 MB", command)
        self.searchoutput(out,
                          "Interface: eth0 00:50:56:01:20:00 \[boot, default_route\]",
                          command)

    def test_555_statusquo(self):
        command = ["update_machine", "--machine=evm1", "--model=utmedium",
                   "--cpucount=1", "--memory=8192"]
        self.noouttest(command)

    def test_560_del_nic_model(self):
        command = ["del", "model", "--model", "default", "--vendor", "utvirt"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model utvirt/default is still in use and cannot be "
                         "deleted.",
                         command)

    def test_600_makecluster(self):
        command = ["make_cluster", "--cluster=utecl1"]
        (out, err) = self.successtest(command)

    def test_700_add_windows(self):
        command = ["add_windows_host", "--hostname=aqddesk1.msad.ms.com",
                   "--osversion=nt61e",
                   "--machine=evm1", "--comments=Windows Virtual Desktop"]
        self.noouttest(command)

    def test_705_verify_vm_status(self):
        command = ["cat", "--cluster", "utecl1", "--virtual_machine", "evm1"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"build", "build",', command)

    def test_800_verify_windows(self):
        command = "show host --hostname aqddesk1.msad.ms.com"

        out = self.commandtest(command.split(" "))

        # core info
        self.searchoutput(out, r"^Virtual_machine: evm1", command)
        self.searchoutput(out, r"^  Primary Name: aqddesk1.msad.ms.com",
                          command)
        self.searchoutput(out, r"^  Comments: Windows Virtual Desktop", command)

        # os
        self.searchoutput(out, r"^    Template: windows/os/windows/nt61e/config"
                          + self.template_extension,
                         command)
        self.searchoutput(out, r"^    Comments: Windows 7 Enterprise \(x86\)",
                          command)

    def test_810_verifycatcluster(self):
        command = "cat --cluster=utecl1 --virtual_machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"name", "windows"', command)
        self.matchoutput(out, '"os", "windows"', command)
        self.matchoutput(out, '"osversion", "nt61e"', command)
        self.matchoutput(out, '"hostname", "aqddesk1"', command)
        self.matchoutput(out, '"domainname", "msad.ms.com"', command)

    def test_820_makecluster(self):
        command = ["make_cluster", "--cluster=utecl1"]
        (out, err) = self.successtest(command)

    # FIXME: Missing a test for add_interface non-esx automac.  (Might not
    # be possible to test with the current command set.)

    # FIXME: we need a more generic test to check if a host/cluster may contain
    # VMs. Perhaps an attribute of Archetype or Personality?
    #def testfailaddnonvirtualcluster(self):
    #    command = ["add", "machine", "--machine", "ut9s03p51",
    #               "--cluster", "utgrid1", "--model", "utmedium"]
    #    out = self.badrequesttest(command)
    #    self.matchoutput(out,
    #                     "Can only add virtual machines to "
    #                     "clusters with archetype esx_cluster.",
    #                     command)

    def testfailaddmissingcluster(self):
        command = ["add_machine", "--machine=ut9s03p51",
                   "--cluster=cluster-does-not-exist", "--model=utmedium"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

    def testfailaddnonvirtual(self):
        command = ["add_machine", "--machine=ut3c1n1", "--model=utmedium",
                   "--chassis=ut3c1.aqd-unittest.ms.com", "--slot=1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Virtual machines must be assigned to a cluster "
                         "or a host.",
                         command)

    def testfailaddnoncluster(self):
        command = ["add_machine", "--machine=ut3c1n1", "--cluster=utecl1",
                   "--model=hs21-8853l5u"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model ibm/hs21-8853l5u is not a virtual machine.",
                         command)

    def testpgnoswitch(self):
        command = ["add", "interface", "--machine", "evm1",
                   "--interface", "eth1", "--pg", "unused-v999"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot verify port group availability: no switch "
                         "record for ESX Cluster utecl1.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
