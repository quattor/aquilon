#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the refresh network command.

These tests don't do much, but they do verify that the command doesn't fail
immediately.

"""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestRefreshNetwork(TestBrokerCommand):

    def testrefreshnetworkdryrun(self):
        command = "refresh network --building np --dryrun"
        out = self.commandtest(command.split(" "))

    def testrefreshnetworkloglevel(self):
        command = "refresh network --building np --loglevel 1"
        out = self.commandtest(command.split(" "))

    def testrefreshnetworkdryrunloglevel(self):
        command = "refresh network --building np --dryrun --loglevel 2"
        out = self.commandtest(command.split(" "))

    def testrefreshnetworkstandard(self):
        command = "refresh network --building np"
        out = self.commandtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)

