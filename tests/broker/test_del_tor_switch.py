#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del tor_switch command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelTorSwitch(TestBrokerCommand):

    def testdelut3gd1r01(self):
        command = "del tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut3gd1r01(self):
        command = "show tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp997gd1r04(self):
        command = "del tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp997gd1r04(self):
        command = "show tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp998gd1r01(self):
        command = "del tor_switch --tor_switch np998gd1r01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp998gd1r01(self):
        command = "show tor_switch --tor_switch np998gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp999gd1r01(self):
        command = "del tor_switch --tor_switch np999gd1r01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp999gd1r01(self):
        command = "show tor_switch --tor_switch np999gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp06bals03(self):
        command = "del tor_switch --tor_switch np06bals03.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp06bals03(self):
        command = "show tor_switch --tor_switch np06bals03.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp06fals01(self):
        command = "del tor_switch --tor_switch np06fals01.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp06bals03(self):
        command = "show tor_switch --tor_switch np06fals01.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s02(self):
        command = "del tor_switch --tor_switch ut01ga1s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut01ga1s02(self):
        command = "show tor_switch --tor_switch ut01ga1s02.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelTorSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

