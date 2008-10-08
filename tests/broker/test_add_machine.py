#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add machine command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddMachine(TestBrokerCommand):

    def testaddut3c5n10(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n10",
            "--rack", "ut3", "--model", "hs21-8853l5u", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--memory", "8192", "--serial", "99C5553"])

    def testverifyaddut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
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

    def testaddut3c1n3(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n3",
            "--chassis", "ut3c1.aqd-unittest.ms.com", "--slot", "3",
            "--model", "hs21-8853l5u", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--memory", "8192", "--serial", "KPDZ406"])

    def testshowslot(self):
        command = "show machine --slot 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testshowchassisslot(self):
        command = "show machine --chassis ut3c1.aqd-unittest.ms.com --slot 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testverifyaddut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ406", command)

    def testverifycatut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "KPDZ406";""",
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

    def testaddut3c1n4(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n4",
            "--rack", "ut3", "--model", "hs21-8853l5u", "--serial", "KPDZ407"])

    def testverifyaddut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n4", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ407", command)

    def testverifycatut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "KPDZ407";""",
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

    # Testing that add machine does not allow a tor_switch....
    def testrejectut3gd2r01(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3gd2r01",
            "--rack", "ut3", "--model", "uttorswitch"])

    def testverifyrejectut3gd2r01(self):
        command = "show machine --machine ut3gd2r01"
        out = self.notfoundtest(command.split(" "))

    # Testing that an invalid cpu returns an error (not an internal error)...
    # (There should be no cpu with speed==2 in the database)
    def testrejectut3c1n5(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3c1n5",
            "--rack", "ut3", "--model", "hs21-8853l5u", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2",
            "--memory", "8192", "--serial", "KPDZ406"])

    def testverifyrejectut3c1n5(self):
        command = "show machine --machine ut3c1n5"
        out = self.notfoundtest(command.split(" "))

    def testrejectmissingmemory(self):
        command = ["add", "machine", "--machine", "ut3c1n6",
            "--rack", "ut3", "--model", "utblade", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--serial", "AAAAAAA"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "does not have machine specification defaults, please specify --memory",
                         command)

    def testverifyrejectmissingmemory(self):
        command = "show machine --machine ut3c1n6"
        out = self.notfoundtest(command.split(" "))

    def testrejectmissingmodel(self):
        command = ["add", "machine", "--machine", "ut3c1n7",
            "--rack", "ut3", "--model", "utblade", "--serial", "BBBBBBB"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "does not have machine specification defaults",
                         command)

    def testverifyrejectmissingmodel(self):
        command = "show machine --machine ut3c1n7"
        out = self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)

