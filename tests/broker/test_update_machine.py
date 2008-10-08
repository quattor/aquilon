#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the update machine command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

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
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
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

    def testupdateut3c1n4(self):
        self.noouttest(["update", "machine", "--machine", "ut3c1n4",
            "--serial", "USNKPDZ407"])

    def testverifyupdateut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n4", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
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
            """"cpu" = list(create("hardware/cpu/intel/xeon_2660"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_2660"));""",
            command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)

