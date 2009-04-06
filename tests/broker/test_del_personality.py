#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del personality command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelPersonality(TestBrokerCommand):

    def testdelutpersonality(self):
        command = "del personality --name utpersonality --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifydelutpersonality(self):
        command = "show personality --name utpersonality --archetype aquilon"
        self.notfoundtest(command.split(" "))

    def testdelwindowsdesktop(self):
        command = "del personality --name desktop --archetype windows"
        self.noouttest(command.split(" "))

    def testverifydelwindowsdesktop(self):
        command = "show personality --name desktop --archetype windows"
        self.notfoundtest(command.split(" "))

    def testdelbadaquilonpersonality(self):
        command = "del personality --name badpersonality --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifydelbadaquilonpersonality(self):
        command = "show personality --name badpersonality --archetype aquilon"
        self.notfoundtest(command.split(" "))

    def testdelbadaquilonpersonality2(self):
        command = "del personality --name badpersonality2 --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifydelbadaquilonpersonality2(self):
        command = "show personality --name badpersonality2 --archetype aquilon"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)

