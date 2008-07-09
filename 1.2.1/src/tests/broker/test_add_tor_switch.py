#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add tor_switch command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddTorSwitch(TestBrokerCommand):

    def testaddut3gd1r01(self):
        self.noouttest(["add", "tor_switch", "--tor_switch", "ut3gd1r01",
            "--rack", "ut3", "--model", "uttorswitch", "--serial", "SNgd1r01"])

    def testverifyaddut3gd1r01(self):
        command = "show tor_switch --tor_switch ut3gd1r01"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Tor_switch: ut3gd1r01", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Model: hp uttorswitch", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2500 x 1", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: SNgd1r01", command)
        for port in range(1,49):
            self.matchoutput(out, "Switch Port %d" % port, command)

    def testverifycatut3gd1r01(self):
        command = "cat --machine ut3gd1r01"
        self.badrequesttest(command.split(" "))

    # Testing that add machine does not allow a tor_switch....
    def testrejectut3gd1r02(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3gd1r02",
            "--rack", "ut3", "--model", "uttorswitch"])

    def testverifyrejectut3gd1r02(self):
        command = "show machine --machine ut3gd1r02"
        out = self.notfoundtest(command.split(" "))

    # Testing that add tor_switch does not allow a blade....
    def testrejectut3gd1r03(self):
        self.badrequesttest(["add", "tor_switch", "--tor_switch", "ut3gd1r03",
            "--rack", "ut3", "--model", "hs21"])

    def testverifyrejectut3gd1r03(self):
        command = "show machine --machine ut3gd1r03"
        out = self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddTorSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

