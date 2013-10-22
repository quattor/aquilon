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
"""Module for testing the add machine command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin
from networktest import DummyIP


class TestAddMachine(MachineTestMixin, TestBrokerCommand):

    def testaddut3c5n10(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n10",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon_2660", "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "99C5553",
                        "--comments", "Some machine comments"])

    def testupdateut3c5n10(self):
        command = ["update", "machine", "--machine", "ut3c5n10",
                   "--ip", self.net["unknown0"].usable[0]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 does not have a primary name.",
                         command)

    def testverifyaddut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)
        self.matchoutput(out, "Comments: Some machine comments", command)
        self.matchclean(out, "Primary Name:", command)

    def testverifydelmodel(self):
        # This should be in test_del_model.py but when that is run there are no
        # more machines defined...
        command = "del model --model hs21-8853l5u --vendor ibm"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Model ibm/hs21-8853l5u is still in use and "
                         "cannot be deleted.", command)

    def testverifycatut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "99C5553";', command)
        # DNS maps:
        # - aqd-unittest.ms.com comes from rack ut3
        # - utroom1 also has aqd-unittest.ms.com mapped _after_ td1 and td2,
        #   but the rack mapping is more specific, so aqd-unittest.ms.com
        #   remains at the beginning
        # - new-york.ms.com comes from the campus
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = list\(\s*'
                          r'"aqd-unittest.ms.com",\s*'
                          r'"td1.aqd-unittest.ms.com",\s*'
                          r'"td2.aqd-unittest.ms.com",\s*'
                          r'"new-york.ms.com"\s*\);',
                          command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    # Used for Zebra tests
    def testaddut3c5n2(self):
        self.create_machine_hs21("ut3c5n2", rack="ut3",
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["zebra_eth0"].usable[0].mac,
                                 eth0_vendor="intel", eth0_model="e1000",
                                 eth1_mac=self.net["zebra_eth1"].usable[0].mac,
                                 eth1_model="e1000")

    # Used for bonding tests
    def testaddut3c5n3(self):
        self.create_machine_hs21("ut3c5n3", rack="ut3",
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["zebra_eth0"].usable[1].mac,
                                 eth1_mac=self.net["zebra_eth1"].usable[1].mac)

    # Used for bridge tests
    def testaddut3c5n4(self):
        self.create_machine_hs21("ut3c5n4", rack="ut3",
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["zebra_eth0"].usable[2].mac,
                                 eth1_mac=self.net["zebra_eth1"].usable[2].mac)

    # Used for house-of-cards location testing
    def testaddjack(self):
        self.noouttest(["add", "machine", "--machine", "jack",
                        "--rack", "cards1", "--model", "hs21-8853l5u"])

    # Used for filer - a fake machine for now
    def testaddfiler(self):
        self.noouttest(["add", "machine", "--machine", "filer1",
                        "--rack", "ut3", "--model", "hs21-8853l5u"])

    # Used for VPLS network tests
    def testaddut3c5n5(self):
        self.create_machine_hs21("ut3c5n5", rack="ut3",
                                 eth0_mac=self.net["vpls"].usable[1].mac)

    # Test normalization
    def testaddnp3c5n5(self):
        self.create_machine_hs21("np3C5N5", rack="np3",
                                 eth0_mac=self.net["vpls"].usable[2].mac)

    def testverifynormalization(self):
        command = "show machine --machine NP3c5N5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: np3c5n5", command)
        self.matchoutput(out, "Model Type: blade", command)

        command = "show machine --machine np3c5n5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: np3c5n5", command)
        self.matchoutput(out, "Model Type: blade", command)

    # Used for testing notifications
    def testaddut3c5n6(self):
        self.create_machine_hs21("ut3c5n6", rack="ut3",
                                 eth0_mac=self.net["unknown0"].usable[19].mac)

    # Network environment testing
    def testaddut3c5n7(self):
        net = self.net["unknown0"]
        self.create_machine_hs21("ut3c5n7", rack="ut3",
                                 interfaces=["eth0", "eth1", "eth2"],
                                 eth0_mac=net.usable[20].mac,
                                 eth1_mac=net.usable[21].mac,
                                 eth2_mac=net.usable[22].mac)

    # Network environment testing
    def testaddut3c5n8(self):
        self.create_machine_hs21("ut3c5n8", rack="ut3",
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["unknown0"].usable[23].mac,
                                 eth1_mac=self.net["routing1"].usable[0].mac)

    def testaddut3c1n3(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n3",
                        "--chassis", "ut3c1.aqd-unittest.ms.com", "--slot", "3",
                        "--model", "hs21-8853l5u", "--cpucount", "2",
                        "--cpuvendor", "intel", "--cpuname", "xeon_2660",
                        "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "KPDZ406"])

    def testshowslot(self):
        command = "search machine --slot 3 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)

    def testshowchassisslot(self):
        command = "search machine --chassis ut3c1.aqd-unittest.ms.com --slot 3 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)

    def testverifyaddut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ406", command)

    def testverifycatut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"rack/name" = "ut3";', command)
        self.matchoutput(out, '"rack/row" = "a";', command)
        self.matchoutput(out, '"rack/column" = "3";', command)
        self.matchoutput(out, '"rack/room" = "utroom1";', command)
        self.matchoutput(out, '"sysloc/room" = "utroom1";', command)
        self.matchoutput(out, '"sysloc/building" = "ut";', command)
        self.matchoutput(out, '"sysloc/city" = "ny";', command)
        self.matchoutput(out, '"sysloc/continent" = "na";', command)
        self.matchoutput(out, '"serialnumber" = "KPDZ406";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    def testaddut3c1n4(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n4",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--serial", "KPDZ407"])

    def testverifyaddut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n4", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ407", command)

    def testverifycatut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "KPDZ407";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    def testaddccissmachine(self):
        self.create_machine("ut3c1n8", "utccissmodel", rack="ut3",
                            eth0_mac=self.net["unknown0"].usable[18].mac)

    def testverifyccissmachine(self):
        command = "show machine --machine ut3c1n8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n8", command)
        self.matchoutput(out, "Model Type: rackmount", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: utccissmodel", command)
        self.matchoutput(out, "Cpu: xeon_2500 x 2", command)
        self.matchoutput(out, "Memory: 49152 MB", command)
        self.matchoutput(out, "Disk: c0d0 466 GB cciss (local) [boot]", command)

    def testverifycatut3c1n8(self):
        command = "cat --machine ut3c1n8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/hp/utccissmodel" };',
                         command)
        self.matchoutput(out,
                         '"harddisks/{cciss/c0d0}" = '
                         'create("hardware/harddisk/generic/cciss",',
                         command)
        self.matchoutput(out,
                         '"capacity", 466*GB',
                         command)

    def testaddut3c1n9(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n9",
                        "--rack", "ut3", "--model", "hs21-8853l5u"])

    def testrejectqualifiedname(self):
        command = ["add", "machine", "--machine", "qualified.ms.com",
                   "--rack", "ut3", "--model", "hs21-8853l5u"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Illegal hardware label format 'qualified.ms.com'.",
                         command)

    # Testing that add machine does not allow a tor_switch....
    def testrejectut3gd2r01(self):
        command = ["add", "machine", "--machine", "ut3gd1r02",
                   "--rack", "ut3", "--model", "uttorswitch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot add machines of type switch",
                         command)

    def testverifyrejectut3gd2r01(self):
        command = "show machine --machine ut3gd2r01"
        out = self.notfoundtest(command.split(" "))

    # Testing that an invalid cpu returns an error (not an internal error)...
    # (There should be no cpu with speed==2 in the database)
    def testrejectut3c1n5(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3c1n5",
                             "--rack", "ut3", "--model", "hs21-8853l5u",
                             "--cpucount", "2", "--cpuvendor", "intel",
                             "--cpuname", "xeon_2660", "--cpuspeed", "2",
                             "--memory", "8192", "--serial", "KPDZ406"])

    def testverifyrejectut3c1n5(self):
        command = "show machine --machine ut3c1n5"
        out = self.notfoundtest(command.split(" "))

    def testrejectmissingmemory(self):
        command = ["add", "machine", "--machine", "ut3c1n6",
                   "--rack", "ut3", "--model", "utblade", "--cpucount", "2",
                   "--cpuvendor", "intel", "--cpuname", "xeon_2500",
                   "--cpuspeed", "2500", "--serial", "AAAAAAA"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "does not have machine specification defaults, please specify --memory",
                         command)

    def testverifyrejectmissingmemory(self):
        command = "show machine --machine ut3c1n6"
        out = self.notfoundtest(command.split(" "))

    def testrejectmissingmodel(self):
        command = ["add", "machine", "--machine", "ut3c1n7", "--rack", "ut3",
                   "--model", "utblade", "--serial", "BBBBBBB"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "does not have machine specification defaults",
                         command)

    def testverifyrejectmissingmodel(self):
        command = "show machine --machine ut3c1n7"
        out = self.notfoundtest(command.split(" "))


    def testrejectmachineuri(self):
        command = ["add", "machine", "--machine", "ut3c1n10",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--uri", "file:///somepath/to/ovf"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "URI can be specified only for virtual "
                                "appliances and the model's type is blade",
                                command)

    def testverifyrejectmachineuri(self):
        command = "show machine --machine ut3c1n10"
        out = self.notfoundtest(command.split(" "))

    # When doing an end-to-end test, these two entries should be
    # created as part of a sweep of a Dell rack.  They represent
    # two mac addresses seen on the same port, only one of which
    # is actually a host.  The other is a management interface.
    def testaddut3s01p1a(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p1a",
                        "--rack", "ut3", "--model", "poweredge_6650"])

    def testverifyaddut3s01p1a(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p1a", command)
        self.matchoutput(out, "Model Type: rackmount", command)

    def testaddut3s01p1b(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p1b",
                        "--rack", "ut3", "--model", "poweredge_6650"])

    def testverifyaddut3s01p1b(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p1b", command)
        self.matchoutput(out, "Model Type: rackmount", command)

    def testaddut3s01p2(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p2",
                        "--rack", "ut3", "--model", "poweredge_6650"])

    def testverifyaddut3s01p2(self):
        command = "show machine --machine ut3s01p2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p2", command)
        self.matchoutput(out, "Model Type: rackmount", command)

    # When doing an end-to-end test, these entries should be
    # created as part of a sweep of a Verari rack
    # (ut01ga1s02.aqd-unittest.ms.com).
    def testaddverariut8(self):
        net = self.net["tor_net_0"]
        for port in range (1, 6):
            machine = "ut8s02p%d" % port
            self.create_machine(machine, "vb1205xm", rack="ut8",
                                eth0_mac=net.usable[port].mac)

    def testaddutnorack(self):
        # A machine that's not in a rack
        self.noouttest(["add", "machine", "--machine", "utnorack",
                        "--desk", "utdesk1", "--model", "poweredge_6650"])

    def testadd10gigracks(self):
        for port in range(1, 13):
            for (template, rack, offset) in [('ut11s01p%d', "ut11", 0),
                                             ('ut12s02p%d', "ut12", 12)]:
                machine = template % port
                # Both counts would start at 0 except the tor_net has two
                # switches taking IPs.
                i = port + 1 + offset
                j = port - 1 + offset
                eth0_mac = self.net["vmotion_net"].usable[i].mac
                eth1_mac = self.net["vm_storage_net"].usable[j].mac
                self.create_machine_verari(machine, rack=rack,
                                           interfaces=["eth0", "eth1"],
                                           eth0_mac=eth0_mac,
                                           eth1_mac=eth1_mac,
                                           eth1_pg="storage-v701")

    def testaddharacks(self):
        # Machines for metacluster high availability testing
        for port in range(1, 25):
            for template, rack, net in [('ut13s03p%d', 'ut13', self.net["esx_bcp_ut"]),
                                        ('np13s03p%d', 'np13', self.net["esx_bcp_np"])]:
                machine = template % port
                self.create_machine_verari(machine, rack=rack,
                                           eth0_mac=net.usable[port].mac)

    def testaddf5test(self):
        ip = DummyIP(self.net["f5test"].ip)
        self.create_machine("f5test", "f5_model", rack="ut3", eth0_mac=ip.mac)

    # FIXME: Missing a test for adding a macihne to a chassis where the
    # fqdn given for the chassis isn't *actually* a chassis.
    # FIXME: Missing a test for chassis without a slot.  (May not be possible
    # with the aq client.)
    # FIXME: Missing a test for a location that conflicts with chassis loc.
    # FIXME: Missing a test for a slot without a chassis.  (May not be possible
    # with the aq client.)
    # FIXME: Add a test where the machine trying to be created already exists.

    # Note: More regression tests are in the test_add_virtual_hardware module.


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
