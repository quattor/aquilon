#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add required service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddRequiredService(TestBrokerCommand):

    def testaddrequiredafs(self):
        command = "add required service --service afs --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifyaddrequiredafs(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs", command)

    def testaddrequireddns(self):
        command = "add required service --service dns --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifyaddrequireddns(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: dns", command)

    def testaddrequiredaqd(self):
        command = "add required service --service aqd --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifyaddrequiredaqd(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)

