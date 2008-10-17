#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the pxeswitch command.

This may have issues being tested somewhere that the command actually works...
"""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestPxeswitch(TestBrokerCommand):
    """Simplified tests for the pxeswitch command.

    Since we can't actually run aii-installfe against imaginary hosts, the
    unittest.conf file specifies /bin/echo as the command to use.  These
    tests just check that the available parameters are passed through
    correctly.

    """

    def testinstallunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --install"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "--install", command)

    def testlocalbootunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --localboot"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "--boot", command)

    def teststatusunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --status"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "--status", command)

    def testinstallunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --firmware"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "--firmware", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPxeswitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

