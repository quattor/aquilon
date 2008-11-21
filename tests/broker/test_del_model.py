#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del model command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelModel(TestBrokerCommand):

    def testdeluttorswitch(self):
        command = "del model --name uttorswitch --vendor hp --type tor_switch"
        self.noouttest(command.split(" "))

    def testverifydeluttorswitch(self):
        command = "show model --name uttorswitch"
        self.notfoundtest(command.split(" "))

    def testdelutblade(self):
        command = "del model --name utblade --vendor aurora_vendor --type blade"
        self.noouttest(command.split(" "))

    def testverifydelutblade(self):
        command = "show model --name utblade"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelModel)
    unittest.TextTestRunner(verbosity=2).run(suite)

