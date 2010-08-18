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
"""Module for testing the update machine command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateMachine(TestBrokerCommand):

    def testupdateut3c1n3(self):
        self.noouttest(["update", "machine", "--machine", "ut3c1n3",
            "--slot", "10", "--serial", "USN99C5553"])

    def testverifyupdateut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 10", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: USN99C5553", command)

    def testverifycatut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "USN99C5553";""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/ibm/hs21-8853l5u' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        # 1st cpu
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_2660"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_2660"));""",
            command)

    def testupdateut3c5n10(self):
        self.noouttest(["update", "machine",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--chassis", "ut3c5.aqd-unittest.ms.com", "--slot", "2"])

    def testverifyshowslot(self):
        command = "show machine --slot 2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)

    def testverifyshowchassisslot(self):
        command = "show machine --chassis ut3c5.aqd-unittest.ms.com --slot 2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)

    def testverifyupdateut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Chassis: ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 2", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)

    def testverifycatut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "99C5553";""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/ibm/hs21-8853l5u' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        # 1st cpu
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_2660"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_2660"));""",
            command)

    def testupdateut3c1n4(self):
        self.noouttest(["update", "machine", "--machine", "ut3c1n4",
            "--serial", "USNKPDZ407"])

    def testupdateut3c1n4cpubadvendor(self):
        self.notfoundtest(["update", "machine", "--machine", "ut3c1n4",
            "--cpuvendor", "no-such-vendor"])

    def testupdateut3c1n4cpubadname(self):
        self.notfoundtest(["update", "machine", "--machine", "ut3c1n4",
            "--cpuname", "no-such-cpu"])

    def testupdateut3c1n4cpureal(self):
        self.noouttest(["update", "machine", "--machine", "ut3c1n4",
            "--cpuname", "xeon_3000"])

    def testverifyupdateut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n4", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_3000 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: USNKPDZ407", command)

    def testverifycatut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "USNKPDZ407";""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/ibm/hs21-8853l5u' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        # 1st cpu
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_3000"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_3000"));""",
            command)

    def testclearchassis(self):
        command = ["update", "machine", "--machine", "ut9s03p1",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "1"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p1",
                   "--clearchassis"]
        self.noouttest(command)

    def testverifyclearchassis(self):
        command = ["show", "machine", "--machine", "ut9s03p1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p1", command)
        self.matchclean(out, "Chassis: ", command)

    def testclearchassisplusnew(self):
        command = ["update", "machine", "--machine", "ut9s03p2",
                   "--chassis", "ut9c5.aqd-unittest.ms.com", "--slot", "1"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p2",
                   "--clearchassis",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "2"]
        self.noouttest(command)

    def testverifyclearchassisplusnew(self):
        command = ["show", "machine", "--machine", "ut9s03p2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p2", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 2", command)

    def testtruechassisupdate(self):
        command = ["update", "machine", "--machine", "ut9s03p3",
                   "--chassis", "ut9c5.aqd-unittest.ms.com", "--slot", "2"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p3",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "3"]
        self.noouttest(command)

    def testverifytruechassisupdate(self):
        command = ["show", "machine", "--machine", "ut9s03p3"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p3", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 3", command)

    def testsimplechassisupdate(self):
        command = ["update", "machine", "--machine", "ut9s03p4",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "4"]
        self.noouttest(command)

    def testverifysimplechassisupdate(self):
        command = ["show", "machine", "--machine", "ut9s03p4"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p4", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 4", command)

    def testsimplechassisupdatewithrack(self):
        # The rack info is redundant but valid
        command = ["update", "machine", "--machine", "ut9s03p5",
                   "--rack", "ut9",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "5"]
        self.noouttest(command)

    def testverifysimplechassisupdatewithrack(self):
        command = ["show", "machine", "--machine", "ut9s03p5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p5", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 5", command)

    def testtruechassisupdatewithrack(self):
        # The rack info is redundant but valid
        command = ["update", "machine", "--machine", "ut9s03p6",
                   "--chassis", "ut9c5.aqd-unittest.ms.com", "--slot", "4"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p6",
                   "--rack", "ut9",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "6"]
        self.noouttest(command)

    def testverifytruechassisupdatewithrack(self):
        command = ["show", "machine", "--machine", "ut9s03p6"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p6", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 6", command)

    def testmissingslot(self):
        command = ["update", "machine", "--machine", "ut9s03p7",
                   "--chassis", "ut9c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Option --chassis requires --slot information",
                         command)

    def testverifymissingslot(self):
        command = ["show", "machine", "--machine", "ut9s03p7"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p7", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def testmissingchassis(self):
        command = ["update", "machine", "--machine", "ut9s03p8",
                   "--slot", "8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Option --slot requires --chassis information",
                         command)

    def testverifymissingchassis(self):
        command = ["show", "machine", "--machine", "ut9s03p8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p8", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def testdifferentrack(self):
        command = ["update", "machine", "--machine", "ut9s03p9",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "9"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p9",
                   "--rack", "ut8"]
        self.noouttest(command)

    def testverifydifferentrack(self):
        command = ["show", "machine", "--machine", "ut9s03p9"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p9", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def testreuseslot(self):
        command = ["update", "machine", "--machine", "ut9s03p10",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "10"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p10",
                   "--clearchassis"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p10",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "10"]
        self.noouttest(command)

    def testverifyreuseslot(self):
        command = ["show", "machine", "--machine", "ut9s03p10"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p10", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 10", command)

    def testtakenslot(self):
        command = ["update", "machine", "--machine", "ut9s03p11",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "11"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p12",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "11"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Chassis ut9c1.aqd-unittest.ms.com slot 11 "
                              "already has machine ut9s03p11", command)

    def testverifyreuseslot(self):
        command = ["show", "machine", "--machine", "ut9s03p11"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p11", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 11", command)
        command = ["show", "machine", "--machine", "ut9s03p12"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p12", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def testmultislotclear(self):
        command = ["update", "machine", "--machine", "ut9s03p13",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "13"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p13",
                   "--multislot",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "14"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p13",
                   "--clearchassis"]
        self.noouttest(command)

    def testverifymultislotclear(self):
        command = ["show", "machine", "--machine", "ut9s03p13"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p13", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def testmultislotadd(self):
        command = ["update", "machine", "--machine", "ut9s03p15",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "1"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p15",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "2"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p15",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "3"]
        self.noouttest(command)

    def testverifymultislotclear(self):
        command = ["show", "machine", "--machine", "ut9s03p15"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p15", command)
        self.matchoutput(out, "Chassis: ut9c2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 1", command)
        self.matchoutput(out, "Slot: 2", command)
        self.matchoutput(out, "Slot: 3", command)

    def testmultislotupdatefail(self):
        command = ["update", "machine", "--machine", "ut9s03p19",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "4"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p19",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "5"]
        self.noouttest(command)
        command = ["update", "machine", "--machine", "ut9s03p19",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "6"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Use --multislot to support a machine in more "
                              "than one slot", command)

    def testverifymultislotclear(self):
        command = ["show", "machine", "--machine", "ut9s03p19"]
        out = self.commandtest(command)
        self.matchoutput(out, "Blade: ut9s03p19", command)
        self.matchoutput(out, "Chassis: ut9c2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 4", command)
        self.matchoutput(out, "Slot: 5", command)
        self.matchclean(out, "Slot: 6", command)

    def testfailmissingcluster(self):
        command = ["update_machine", "--machine=evm1",
                   "--cluster=cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def testfailchangemetacluster(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl4"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot move machine to a new "
                         "metacluster: Current metacluster utmc1 "
                         "does not match new metacluster utmc2",
                         command)

    def testfailfullcluster(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl3"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl3 cannot support VMs with "
                         "0 vmhosts and a down_host_threshold of 2",
                         command)

    def testfailaddreadmachinetocluster(self):
        command = ["update_machine", "--machine=ut9s03p19", "--cluster=utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cannot add an existing machine to a cluster.",
                         command)

    # These tests would be nice, but twisted just ignores the permission
    # on the files since we're still the owner.  Which is good, but means
    # the recovery routines can't be easily tested.
#   def testfailbrokenplenary(self):
#       template = os.path.join(self.config.get("broker", "plenarydir"),
#                               "machine", "americas", "ut", "ut9",
#                               "ut9s03p20.tpl")
#       os.chmod(template, 0000)
#       command = ["update_machine", "--machine=ut9s03p20", "--serial=20"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out, "FIXME", command)

#   def testverifyfailbrokenplenary(self):
#       # Fixing the previous breakage... not actually necessary for this test.
#       template = os.path.join(self.config.get("broker", "plenarydir"),
#                               "machine", "americas", "ut", "ut9",
#                               "ut9s03p20.tpl")
#       os.chmod(template, 0644)
#       command = ["show_machine", "--machine=ut9s03p20"]
#       out = self.commandtest(command)
#       self.matchclean(out, "Serial", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)

