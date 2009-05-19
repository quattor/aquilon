#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the update archetype command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUpdateArchetype(TestBrokerCommand):

    def testupdatecompilable(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--compilable"])

    def testupdatenotcompilable(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype2",
                        "--compilable"])
        self.noouttest(["update_archetype", "--archetype=utarchetype2"])

    def testverifycompilable(self):
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1 [compilable]", command)

    def testverifynotcompilable(self):
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype2", command)
        self.matchclean(out, "compilable", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)

