#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints in commands involving machine."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMachineConstraints(TestBrokerCommand):

    def testdelmachinewithhost(self):
        command = "del machine --machine ut3c5n10"
        self.badrequesttest(command.split(" "))

    def testverifydelmachinewithhostfailed(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)

    # Expected to fail without the --all flag...
    def testdelalldisks(self):
        command = "del disk --machine ut3c5n10"
        self.badrequesttest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMachineConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)

