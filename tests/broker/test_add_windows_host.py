#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add windows host command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddWindowsHost(TestBrokerCommand):

    def testaddunittest01(self):
        self.noouttest(["add", "windows", "host",
            "--hostname", "unittest01.one-nyp.ms.com", "--ip", self.hostip4,
            "--machine", "ut3c1n4"])

    def testverifyaddunittest01(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip4, command)
        self.matchoutput(out, "Blade: ut3c1n4", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Build Status: build", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddWindowsHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
