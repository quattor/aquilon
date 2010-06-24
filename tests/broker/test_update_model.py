#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the update model command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestUpdateModel(TestBrokerCommand):

    def test_000_sanitycheck(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"ram" = list(create("hardware/ram/generic", '
                         '"size", 8192*MB));',
                         command)
        self.matchoutput(out, 'create("hardware/cpu/intel/xeon_2500")',
                         command)
        self.matchoutput(out, "'capacity', 15*GB,", command)
        self.matchoutput(out, "'interface', 'sata',", command)

    def test_100_updateexisting(self):
        command = ["update_model", "--model=utmedium", "--vendor=utvendor",
                   "--cpuname=utcpu", "--cpunum=1", "--memory=4096", "--nics=1",
                   "--disksize=45", "--diskcontroller=scsi"]
        self.noouttest(command)

    def test_110_verifyspecs(self):
        command = ["show_model", "--model=utmedium"]
        out = self.commandtest(command)
        self.matchoutput(out, "MachineSpecs for utvendor utmedium:",
                         command)
        self.matchoutput(out, "Cpu: utcpu x 1", command)
        self.matchoutput(out, "Memory: 4096 MB", command)
        self.matchoutput(out, "NIC count: 1", command)
        self.matchoutput(out, "Disk: sda 45 GB DiskType scsi [nas]", command)

    def test_120_verifymachine(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"ram" = list(create("hardware/ram/generic", '
                         '"size", 4096*MB));',
                         command)
        self.matchoutput(out, 'create("hardware/cpu/intel/utcpu")',
                         command)
        self.matchoutput(out, "'capacity', 45*GB,", command)
        self.matchoutput(out, "'interface', 'scsi',", command)

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
        self.matchoutput(out, "Disk: sda 45 GB DiskType scsi [local]", command)

    def test_230_verifymachine(self):
        command = ["cat", "--machine=evm1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"ram" = list(create("hardware/ram/generic", '
                         '"size", 4096*MB));',
                         command)
        self.matchoutput(out, 'create("hardware/cpu/intel/utcpu")',
                         command)
        self.matchoutput(out, "'capacity', 45*GB,", command)
        self.matchoutput(out, "'interface', 'scsi',", command)

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
                         "include { 'hardware/machine/utvendor/utmedium-v1' }",
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
                         "include { 'hardware/machine/virtual/utmedium-v1' }",
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
                         "include { 'hardware/machine/utvendor/utmedium' }",
                         command)

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
                   "--disktype=local", "--diskcontroller=scsi",
                   "--disksize=30", "--nics=2", "--leave_existing"]
        self.noouttest(command)

    def test_810_verifyspecs(self):
        command = ["show_model", "--model=utblade"]
        out = self.commandtest(command)
        self.matchoutput(out, "MachineSpecs for aurora_vendor utblade:",
                         command)
        self.matchoutput(out, "Cpu: utcpu x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "NIC count: 2", command)
        self.matchoutput(out, "Disk: sda 30 GB DiskType scsi [local]", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
