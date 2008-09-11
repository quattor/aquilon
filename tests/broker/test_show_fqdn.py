#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the show fqdn command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowFqdn(TestBrokerCommand):

    def testshowfqdnall(self):
        command = "show fqdn --all"
        out = self.commandtest(command.split(" "))
        # Chassis
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        # TorSwitch
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        # Aurora Host
        self.matchoutput(out, "pissp1.ms.com", command)
        # Aquilon Host
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        # Auxiliary
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        # Windows Host
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowFqdn)
    unittest.TextTestRunner(verbosity=2).run(suite)

