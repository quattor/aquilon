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
        command = ["del_personality", "--personality=utpersonality",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelutpersonality(self):
        command = ["show_personality", "--personality=utpersonality",
                   "--archetype=aquilon"]
        self.notfoundtest(command)

    def testdelwindowsdesktop(self):
        command = "del personality --personality desktop --archetype windows"
        self.noouttest(command.split(" "))

    def testverifydelwindowsdesktop(self):
        command = "show personality --personality desktop --archetype windows"
        self.notfoundtest(command.split(" "))

    def testdelbadaquilonpersonality(self):
        command = ["del_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelbadaquilonpersonality(self):
        command = ["show_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        self.notfoundtest(command)

    def testdelbadaquilonpersonality2(self):
        command = ["del_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelbadaquilonpersonality2(self):
        command = ["show_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        self.notfoundtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)

