#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the get domain command."""

import os
import sys
import unittest
from subprocess import Popen

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestGetDomain(TestBrokerCommand):

    def testclearchangetest1domain(self):
        p = Popen(("/bin/rm", "-rf",
            os.path.join(self.scratchdir, "changetest1")), stdout=1, stderr=2)
        rc = p.wait()

    def testclearchangetest2domain(self):
        p = Popen(("/bin/rm", "-rf",
            os.path.join(self.scratchdir, "changetest2")), stdout=1, stderr=2)
        rc = p.wait()

    def testclearunittestdomain(self):
        p = Popen(("/bin/rm", "-rf",
            os.path.join(self.scratchdir, "unittest")), stdout=1, stderr=2)
        rc = p.wait()

    def testgetchangetest1domain(self):
        self.ignoreoutputtest(["get", "--domain", "changetest1"],
                cwd=self.scratchdir)
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest1")))

    def testgetchangetest2domain(self):
        self.ignoreoutputtest(["get", "--domain", "changetest2"],
                cwd=self.scratchdir)
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest2")))

    def testgetunittestdomain(self):
        self.ignoreoutputtest(["get", "--domain", "unittest"],
                cwd=self.scratchdir)
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "unittest")))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGetDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

