#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the status command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestStatus(TestBrokerCommand):

    def teststatus(self):
        command = "status"
        out = self.commandtest(command)
        # This used to confirm the version, but that seems somewhat
        # pointless since it's now dynamic (based on `git describe`).
        # Just making sure something comes out...
        self.matchoutput(out, "Aquilon Broker ", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)

