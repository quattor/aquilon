#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add personality command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddPersonality(TestBrokerCommand):

    def testaddutpersonality(self):
        command = "add personality --name utpersonality --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifyaddutpersonality(self):
        command = "show personality --name utpersonality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: personality/utpersonality", command)

    def testverifyshowpersonalityall(self):
        command = "show personality --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: personality/utpersonality", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)

