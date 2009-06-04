#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del archetype command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelArchetype(TestBrokerCommand):

    def testdelutarchetype1(self):
        command = ["del_archetype", "--archetype=utarchetype1"]
        self.noouttest(command)

    def testdelutarchetype2(self):
        command = ["del_archetype", "--archetype=utarchetype2"]
        self.noouttest(command)

    def testverifydelutarchetype1(self):
        command = ["show_archetype", "--archetype=utarchetype1"]
        self.notfoundtest(command)

    def testverifydelutarchetype2(self):
        command = ["show_archetype", "--archetype=utarchetype2"]
        self.notfoundtest(command)

    def testverifyall(self):
        command = ["show_archetype", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Archetype: utarchetype", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)

