#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelService(TestBrokerCommand):

    def testdelafsinstance(self):
        self.noouttest(["del", "service",
            "--service", "afs", "--instance", "q.ny.ms.com"])

    def testdelbootserverinstance(self):
        self.noouttest(["del", "service",
            "--service", "bootserver", "--instance", "np.test"])

    def testdeldnsinstance(self):
        self.noouttest(["del", "service",
            "--service", "dns", "--instance", "nyinfratest"])

    def testdelntpinstance(self):
        self.noouttest(["del", "service",
            "--service", "ntp", "--instance", "pa.ny.na"])

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelService)
    unittest.TextTestRunner(verbosity=2).run(suite)

