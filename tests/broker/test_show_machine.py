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
"""Module for testing the show machine command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestShowMachine(TestBrokerCommand):
    def testverifymachineall(self):
        command = ["show", "machine", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3c5n10", command)
        self.matchoutput(out, "ut3c1n3", command)
        self.matchoutput(out, "ut3c1n4", command)
        self.matchoutput(out, "ut3s01p1", command)
        self.matchoutput(out, "ut8s02p1", command)
        self.matchoutput(out, "ut9s03p1", command)
        self.matchoutput(out, "ut10s04p1", command)
        self.matchoutput(out, "ut11s01p1", command)
        self.matchoutput(out, "f5test", command)
        self.matchclean(out, "ut3s01p1a", command)
        self.matchclean(out, "ut3s01p1b", command)

    def testverifyut3c1n3interfacescsv(self):
        command = "show machine --machine ut3c1n3 --format csv"
        out = self.commandtest(command.split(" "))
        net = self.net["unknown0"]
        self.matchoutput(out,
                         "ut3c1n3,ut3,ut,ibm,hs21-8853l5u,KPDZ406,eth0,%s,%s" %
                         (net.usable[2].mac, net.usable[2]), command)
        self.matchoutput(out,
                         "ut3c1n3,ut3,ut,ibm,hs21-8853l5u,KPDZ406,eth1,%s,%s" %
                         (net.usable[3].mac, net.usable[3]), command)
        self.matchoutput(out,
                         "ut3c1n3,ut3,ut,ibm,hs21-8853l5u,KPDZ406,bmc,%s,%s" %
                         (net.usable[4].mac, net.usable[4]), command)

    def testrejectfqdn(self):
        command = "show machine --machine unittest00.one-nyp.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Illegal hardware label", command)

    def testshowproto(self):
        command = ["show_machine", "--machine", "ut3c1n3", "--format", "proto"]
        out = self.commandtest(command)
        machinelist = self.parse_machine_msg(out, expect=1)
        machine = machinelist.machines[0]
        self.assertEqual(machine.name, "ut3c1n3")
        self.assertEqual(machine.host, "unittest00.one-nyp.ms.com")
        self.assertEqual(machine.location.name, "ut3")
        self.assertEqual(machine.model.name, "hs21-8853l5u")
        self.assertEqual(machine.model.vendor, "ibm")
        self.assertEqual(machine.model.model_type, "blade")
        self.assertEqual(machine.cpu, "xeon_2660")
        self.assertEqual(machine.cpu_count, 2)
        self.assertEqual(machine.memory, 8192)
        self.assertEqual(machine.serial_no, "KPDZ406")
        self.assertEqual(len(machine.interfaces), 3)
        self.assertEqual(len(machine.disks), 2)
        self.assertEqual(machine.disks[0].device_name, "c0d0")
        self.assertEqual(machine.disks[0].disk_type, "cciss")
        self.assertEqual(machine.disks[0].capacity, 34)
        self.assertEqual(machine.disks[0].address, "")
        self.assertEqual(machine.disks[0].bus_address, "pci:0000:01:00.0")
        self.assertEqual(machine.disks[0].wwn,
                         "600508b112233445566778899aabbccd")
        self.assertEqual(machine.disks[1].device_name, "sda")
        self.assertEqual(machine.disks[1].disk_type, "scsi")
        self.assertEqual(machine.disks[1].capacity, 68)
        self.assertEqual(machine.disks[1].address, "")
        self.assertEqual(machine.disks[1].bus_address, "")
        self.assertEqual(machine.disks[1].wwn, "")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
