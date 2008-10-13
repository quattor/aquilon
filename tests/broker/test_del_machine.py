#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del machine command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelMachine(TestBrokerCommand):

    def testdelut3c5n10(self):
        command = "del machine --machine ut3c5n10"
        self.noouttest(command.split(" "))

    def testverifydelut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n3(self):
        command = "del machine --machine ut3c1n3"
        self.noouttest(command.split(" "))

    def testverifydelut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n4(self):
        command = "del machine --machine ut3c1n4"
        self.noouttest(command.split(" "))

    def testverifydelut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        self.notfoundtest(command.split(" "))

    def testdelut3s01p1(self):
        command = "del machine --machine ut3s01p1"
        self.noouttest(command.split(" "))

    def testverifydelut3s01p1(self):
        command = "show machine --machine ut3s01p1"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p1(self):
        command = "del machine --machine ut8s02p1"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p1(self):
        command = "show machine --machine ut8s02p1"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p2(self):
        command = "del machine --machine ut8s02p2"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p2(self):
        command = "show machine --machine ut8s02p2"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p3(self):
        command = "del machine --machine ut8s02p3"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p3(self):
        command = "show machine --machine ut8s02p3"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)

