#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the update model command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateModel(TestBrokerCommand):

    def test_000_sanitycheck(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_5150"\)\s*\);',
                          command)
        self.matchoutput(out, '"capacity", 15*GB,', command)
        self.matchoutput(out, '"interface", "sata",', command)

    def test_100_updateexisting(self):
        command = ["update_model", "--model=utmedium", "--vendor=utvendor",
                   "--cpuname=utcpu", "--cpunum=1", "--memory=4096", "--nics=1",
                   "--disksize=45", "--diskcontroller=scsi",
                   "--comments", "New model comments"]
        self.noouttest(command)

    def test_110_verifyspecs(self):
        command = ["show_model", "--model=utmedium"]
        out = self.commandtest(command)
        self.matchoutput(out, "MachineSpecs for utvendor utmedium:",
                         command)
        self.matchoutput(out, "Cpu: utcpu x 1", command)
        self.matchoutput(out, "Memory: 4096 MB", command)
        self.matchoutput(out, "NIC count: 1", command)
        self.matchoutput(out, "Disk: sda 45 GB scsi (virtual_disk)", command)
        self.matchoutput(out, "Comments: New model comments", command)

    def test_110_verify_search(self):
        command = ["search", "model", "--cpuname", "utcpu"]
        out = self.commandtest(command)
        self.matchoutput(out, "utvendor/utmedium", command)
        self.matchclean(out, "utlarge", command)
        self.matchclean(out, "ibm", command)

    def test_120_verifymachine(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 4096\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/utcpu"\)\s*\);',
                          command)
        self.matchoutput(out, '"capacity", 45*GB,', command)
        self.matchoutput(out, '"interface", "scsi",', command)

    def test_200_faildisktype(self):
        command = ["update_model", "--model=utmedium", "--vendor=utvendor",
                   "--cpuname=utcpu", "--cpuvendor=intel",
                   "--cpuspeed=1000", "--disktype=local"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "This cannot be converted automatically.",
                         command)

    def test_210_updatedisktype(self):
        command = ["update_model", "--model=utmedium", "--vendor=utvendor",
                   "--cpuname=xeon_2660", "--cpuvendor=intel",
                   "--cpuspeed=2660", "--disktype=local", "--leave_existing"]
        self.noouttest(command)

    def test_220_verifyspecs(self):
        command = ["show_model", "--model=utmedium"]
        out = self.commandtest(command)
        self.matchoutput(out, "MachineSpecs for utvendor utmedium:",
                         command)
        self.matchoutput(out, "Cpu: xeon_2660 x 1", command)
        self.matchoutput(out, "Memory: 4096 MB", command)
        self.matchoutput(out, "NIC count: 1", command)
        self.matchoutput(out, "Disk: sda 45 GB scsi (local)", command)

    def test_230_verifymachine(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 4096\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/utcpu"\)\s*\);',
                          command)
        self.matchoutput(out, '"capacity", 45*GB,', command)
        self.matchoutput(out, '"interface", "scsi",', command)

    def test_300_updatetype(self):
        command = ["update_model", "--model=utblade", "--vendor=aurora_vendor",
                   "--machine_type=rackmount"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "Cannot (yet) change a model's machine type",
                         command)

    def test_301_leavevendor(self):
        command = ["update_model", "--model=utmedium", "--vendor=utvendor",
                   "--newmodel=utmedium-v1", "--leave_existing"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot update model name or vendor without "
                         "updating any existing machines",
                         command)

    def test_302_dupename(self):
        command = ["update_model", "--model=utblade", "--vendor=aurora_vendor",
                   "--newmodel=utmedium", "--newvendor=utvendor"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model utmedium, vendor utvendor already exists.",
                         command)

    def test_310_updatename(self):
        command = ["update_model", "--model=utmedium", "--vendor=utvendor",
                   "--newmodel=utmedium-v1"]
        self.noouttest(command)

    def test_311_verifyname(self):
        command = ["show_model", "--model=utmedium-v1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: utvendor Model: utmedium-v1", command)

    def test_312_verifycat(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'include { "hardware/machine/utvendor/utmedium-v1" }',
                         command)

    def test_320_updatevendor(self):
        command = ["update_model", "--model=utmedium-v1", "--vendor=utvendor",
                   "--newvendor=virtual"]
        self.noouttest(command)

    def test_321_verifyvendor(self):
        command = ["show_model", "--model=utmedium-v1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: virtual Model: utmedium-v1", command)

    def test_322_verifycat(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'include { "hardware/machine/virtual/utmedium-v1" }',
                         command)

    def test_330_restore(self):
        command = ["update_model", "--model=utmedium-v1", "--vendor=virtual",
                   "--newvendor=utvendor", "--newmodel=utmedium"]
        self.noouttest(command)

    def test_331_verifyupdate(self):
        command = ["show_model", "--model=utmedium"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)

    def test_332_verifycat(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'include { "hardware/machine/utvendor/utmedium" }',
                         command)

    def test_340_evm1_utlarge(self):
        command = ["update", "machine", "--machine", "evm1", "--model", "utlarge"]
        self.noouttest(command)

    def test_341_verify_update(self):
        command = ["cat", "--machine", "evm1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "00:50:56:01:20:00"\s*\)\s*\);',
                          command)

    def test_342_update_nic(self):
        command = ["update", "model", "--model", "utlarge", "--vendor", "utvendor",
                   "--nicvendor", "utvirt", "--nicmodel", "default"]
        self.noouttest(command)

    def test_343_verify_model_update(self):
        command = ["show", "model", "--model", "utlarge"]
        out = self.commandtest(command)
        self.matchoutput(out, "NIC Vendor: utvirt Model: default", command)

    def test_343_verify_machine(self):
        command = ["cat", "--machine", "evm1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/utvirt/default",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "00:50:56:01:20:00"\s*\)\s*\);',
                          command)

    def test_344_change_evm1_back(self):
        command = ["update", "machine", "--machine", "evm1", "--model", "utmedium"]
        self.noouttest(command)

    def test_700_failnospecs(self):
        command = ["update_model", "--model=utblade", "--vendor=aurora_vendor",
                   "--memory=8192"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Missing required parameters to store", command)

    def test_710_verifyfail(self):
        command = ["show_model", "--model=utblade"]
        out = self.commandtest(command)
        self.matchclean(out, "MachineSpecs", command)

    def test_800_addspecs(self):
        command = ["update_model", "--model=utblade", "--vendor=aurora_vendor",
                   "--cpuname=utcpu", "--cpunum=2", "--memory=8192",
                   "--disktype=local", "--diskcontroller=scsi", "--disksize=30",
                   "--nics=2", "--nicmodel=generic_nic", "--nicvendor=generic",
                   "--leave_existing"]
        self.noouttest(command)

    def test_810_verifyspecs(self):
        command = ["show_model", "--model=utblade"]
        out = self.commandtest(command)
        self.matchoutput(out, "MachineSpecs for aurora_vendor utblade:",
                         command)
        self.matchoutput(out, "Cpu: utcpu x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "NIC count: 2", command)
        self.matchoutput(out, "Disk: sda 30 GB scsi (local)", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
