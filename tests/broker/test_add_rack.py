#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add rack command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddRack(TestBrokerCommand):

    def testaddut3(self):
        command = "add rack --rackid 3 --building ut --row a --column 3"
        self.noouttest(command.split(" "))

    def testverifyaddut3(self):
        command = "show rack --name ut3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Row: a", command)
        self.matchoutput(out, "Column: 3", command)

    def testaddnp997(self):
        command = "add rack --rackid np997 --building np --row ZZ --column 99"
        self.noouttest(command.split(" "))

    def testverifyaddnp997(self):
        command = "show rack --name np997"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np997", command)
        self.matchoutput(out, "Row: zz", command)
        self.matchoutput(out, "Column: 99", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRack)
    unittest.TextTestRunner(verbosity=2).run(suite)

