#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add building command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddBuilding(TestBrokerCommand):

    def testaddut(self):
        command = "add building --name ut --city ny"
        self.noouttest(command.split(" "))

    def testverifyaddut(self):
        command = "show building --name ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: ut", command)

    def testverifyshowcsv(self):
        command = "show building --name ut --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "building,ut,city,ny", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)

