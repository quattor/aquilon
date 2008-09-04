#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints in commands involving tor_switch."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestTorSwitchConstraints(TestBrokerCommand):

    def testdelmachineastor_switch(self):
        command = "del tor_switch --tor_switch ut3c5n10"
        self.badrequesttest(command.split(" "))

    def testverifydelmachineastor_switchfailed(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)

    # This test doesn't make sense right now.
    #def testdeltor_switchasmachine(self):
    #    command = "del machine --machine ut3gd1r01.aqd-unittest.ms.com"
    #    self.badrequesttest(command.split(" "))

    def testverifydeltor_switchasmachinefailed(self):
        command = "show tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Tor_switch: ut3gd1r01.aqd-unittest.ms.com",
                         command)

    # Testing that del tor_switch does not delete a blade....
    def testrejectut3c1n3(self):
        self.badrequesttest(["del", "tor_switch", "--tor_switch", "ut3c1n3"])

    def testverifyrejectut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTorSwitchConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)

