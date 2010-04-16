#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Module for testing the add model command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddModel(TestBrokerCommand):

    def testadduttorswitch(self):
        command = ["add_model", "--name=uttorswitch", "--vendor=hp",
                   "--type=tor_switch", "--cputype=xeon_2500", "--cpunum=1",
                   "--mem=8192", "--disktype=local", "--diskcontroller=scsi",
                   "--disksize=36", "--nics=4"]
        self.noouttest(command)

    def testverifyadduttorswitch(self):
        command = "show model --name uttorswitch"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)
        self.matchoutput(out, "Type: tor_switch", command)
        self.matchoutput(out, "MachineSpecs for hp uttorswitch", command)
        self.matchoutput(out, "Cpu: xeon_2500 x 1", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "NIC count: 4", command)
        self.matchoutput(out, "Disk: sda 36 GB DiskType scsi", command)

    def testverifyshowtypetorswitch(self):
        command = "show model --type tor_switch"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testverifyshowtypeblade(self):
        command = "show model --type blade"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Vendor: hp Model: uttorswitch", command)

    def testverifyshowvendorhp(self):
        command = "show model --vendor hp"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testverifyshowvendoribm(self):
        command = "show model --vendor ibm"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Vendor: hp Model: uttorswitch", command)

    def testverifyshowall(self):
        command = "show model --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testaddutchassis(self):
        command = "add model --name utchassis --vendor aurora_vendor --type chassis"
        self.noouttest(command.split(" "))

    def testverifyaddutchassis(self):
        command = "show model --name utchassis"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: aurora_vendor Model: utchassis", command)
        self.matchoutput(out, "Type: chassis", command)

    def testaddutblade(self):
        command = "add model --name utblade --vendor aurora_vendor --type blade"
        self.noouttest(command.split(" "))

    def testverifyaddutblade(self):
        command = "show model --name utblade"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: aurora_vendor Model: utblade", command)
        self.matchoutput(out, "Type: blade", command)

    def testaddutmedium(self):
        command = ["add_model", "--name=utmedium", "--vendor=utvendor",
                   "--type=virtual_machine", "--cputype=xeon_2500",
                   "--cpunum=1", "--mem=8192", "--disktype=nas",
                   "--diskcontroller=sata", "--disksize=15", "--nics=1"]
        self.noouttest(command)

    def testaddutlarge(self):
        command = ["add_model", "--name=utlarge", "--vendor=utvendor",
                   "--type=virtual_machine", "--cputype=xeon_2660",
                   "--cpunum=4", "--mem=16384", "--disktype=nas",
                   "--diskcontroller=sata", "--disksize=45", "--nics=1"]
        self.noouttest(command)

    def testverifyaddutmedium(self):
        command = "show model --name utmedium"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)
        self.matchoutput(out, "Type: virtual_machine", command)

    def testfailauroranode(self):
        command = ["add_model", "--name=invalid", "--vendor=aurora_vendor",
                   "--type=aurora_node"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The model's machine type must be one of",
                         command)

    def testfailduplicate(self):
        command = ["add_model", "--name=utblade", "--vendor=aurora_vendor",
                   "--type=blade"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Specified model already exists", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
