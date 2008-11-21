#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del rack command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelRack(TestBrokerCommand):

    def testdelut3(self):
        command = "del rack --name ut3"
        self.noouttest(command.split(" "))

    def testverifydelut3(self):
        command = "show rack --name ut3"
        self.notfoundtest(command.split(" "))

    def testdelnp997(self):
        command = "del rack --name np997"
        self.noouttest(command.split(" "))

    def testverifydelnp997(self):
        command = "show rack --name np997"
        self.notfoundtest(command.split(" "))

    # Created by test_add_tor_switch
    def testdelnp998(self):
        command = "del rack --name np998"
        self.noouttest(command.split(" "))

    def testverifydelnp998(self):
        command = "show rack --name np998"
        self.notfoundtest(command.split(" "))

    # Created by test_add_tor_switch
    def testdelnp999(self):
        command = "del rack --name np999"
        self.noouttest(command.split(" "))

    def testverifydelnp999(self):
        command = "show rack --name np999"
        self.notfoundtest(command.split(" "))

    # FIXME: Maybe del_tor_switch should remove the rack if it is
    # otherwise empty.
    def testdelut8(self):
        command = "del rack --name ut8"
        self.noouttest(command.split(" "))

    def testverifydelut8(self):
        command = "show rack --name ut8"
        self.notfoundtest(command.split(" "))

    def testdelut9(self):
        command = "del rack --name ut9"
        self.noouttest(command.split(" "))

    def testverifydelut9(self):
        command = "show rack --name ut9"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRack)
    unittest.TextTestRunner(verbosity=2).run(suite)

