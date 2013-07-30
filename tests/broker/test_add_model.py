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
"""Module for testing the add model command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddModel(TestBrokerCommand):

    def test_100_adduttorswitch(self):
        command = ["add_model", "--model=uttorswitch", "--vendor=hp",
                   "--type=switch", "--cpuname=xeon_2500", "--cpunum=1",
                   "--memory=8192", "--disktype=local", "--diskcontroller=scsi",
                   "--disksize=36", "--nics=4",
                   "--comments", "Some model comments"]
        self.noouttest(command)

    def test_200_verifyadduttorswitch(self):
        command = "show model --model uttorswitch"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)
        self.matchoutput(out, "Type: switch", command)
        self.matchoutput(out, "MachineSpecs for hp uttorswitch", command)
        self.matchoutput(out, "Cpu: xeon_2500 x 1", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "NIC count: 4", command)
        self.matchoutput(out, "Disk: sda 36 GB scsi (local)", command)
        self.matchoutput(out, "Comments: Some model comments", command)

    def test_200_verifyshowtypetorswitch(self):
        command = "show model --type switch"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def test_200_verifyshowtypeblade(self):
        command = "show model --type blade"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Vendor: hp Model: uttorswitch", command)

    def test_200_verifyshowvendorhp(self):
        command = "show model --vendor hp"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def test_200_verifyshowvendoribm(self):
        command = "show model --vendor ibm"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Vendor: hp Model: uttorswitch", command)

    def test_200_verifyshowall(self):
        command = "show model --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def test_100_addutchassis(self):
        command = "add model --model utchassis --vendor aurora_vendor --type chassis"
        self.noouttest(command.split(" "))

    def test_200_verifyaddutchassis(self):
        command = "show model --model utchassis"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: aurora_vendor Model: utchassis", command)
        self.matchoutput(out, "Type: chassis", command)

    def test_100_addutblade(self):
        command = "add model --model utblade --vendor aurora_vendor --type blade"
        self.noouttest(command.split(" "))

    def test_200_verifyaddutblade(self):
        command = "show model --model utblade"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: aurora_vendor Model: utblade", command)
        self.matchoutput(out, "Type: blade", command)

    def test_100_adde1000(self):
        command = ["add", "model", "--type", "nic", "--model", "e1000",
                   "--vendor", "intel"]
        self.noouttest(command)

    def test_100_addvmnic(self):
        command = ["add", "model", "--type", "nic", "--model", "default",
                   "--vendor", "utvirt"]
        self.noouttest(command)

    def test_110_addutmedium(self):
        # Use the old --mem name here
        command = ["add_model", "--model=utmedium", "--vendor=utvendor",
                   "--type=virtual_machine", "--cpuname=xeon_5150",
                   "--cpunum=1", "--mem=8192", "--disktype=virtual_disk",
                   "--diskcontroller=sata", "--disksize=15", "--nics=1",
                   "--nicmodel", "default", "--nicvendor", "utvirt"]
        self.noouttest(command)

    def test_100_addutlarge(self):
        command = ["add_model", "--model=utlarge", "--vendor=utvendor",
                   "--type=virtual_machine", "--cpuname=xeon_5150",
                   "--cpunum=4", "--memory=16384", "--disktype=virtual_disk",
                   "--diskcontroller=sata", "--disksize=45", "--nics=1"]
        self.noouttest(command)

    def test_200_verifyaddutmedium(self):
        command = "show model --model utmedium"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)
        self.matchoutput(out, "Type: virtual_machine", command)
        self.matchoutput(out, "NIC Vendor: utvirt Model: default", command)

    def test_300_failauroranode(self):
        command = ["add_model", "--model=invalid", "--vendor=aurora_vendor",
                   "--type=aurora_node"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The model's machine type must be one of",
                         command)

    def test_300_failduplicate(self):
        command = ["add_model", "--model=utblade", "--vendor=aurora_vendor",
                   "--type=blade"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model utblade, vendor aurora_vendor already "
                         "exists.", command)

    def test_100_addutccissmodel(self):
        command = ["add_model", "--model=utccissmodel", "--vendor=hp",
                   "--type=rackmount", "--cpuname=xeon_2500", "--cpunum=2",
                   "--memory=49152", "--disktype=local",
                   "--diskcontroller=cciss",
                   "--disksize=466", "--nics=2"]
        self.noouttest(command)

    def test_200_verifyaddutccissmodel(self):
        command = "show model --model utccissmodel"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: utccissmodel", command)
        self.matchoutput(out, "Type: rackmount", command)
        self.matchoutput(out, "MachineSpecs for hp utccissmodel", command)
        self.matchoutput(out, "Cpu: xeon_2500 x 2", command)
        self.matchoutput(out, "Memory: 49152 MB", command)
        self.matchoutput(out, "NIC count: 2", command)
        self.matchoutput(out, "Disk: c0d0 466 GB cciss (local)",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
