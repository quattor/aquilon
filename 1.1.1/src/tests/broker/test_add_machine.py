#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
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
            "--chassis", "ut3c5", "--model", "hs21", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--memory", "8192", "--serial", "99C5553"])

    def testverifyaddut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Chassis: ut3c5", command)
        self.matchoutput(out, "Model: ibm hs21", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)

    def testverifycatut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "np.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "99C5553";""",
            command)
        self.matchoutput(out,
            """include hardware/machine/ibm/hs21;""",
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

    # FIXME: Turn this into a test for model defaults...
    def testaddut3c1n3(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n3",
            "--chassis", "ut3c1", "--model", "hs21", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--memory", "8192", "--serial", "KPDZ406"])

    def testverifyaddut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Chassis: ut3c1", command)
        self.matchoutput(out, "Model: ibm hs21", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ406", command)

    def testverifycatut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "np.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "KPDZ406";""",
            command)
        self.matchoutput(out,
            """include hardware/machine/ibm/hs21;""",
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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)

