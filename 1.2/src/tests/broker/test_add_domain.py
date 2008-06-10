#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddDomain(TestBrokerCommand):

    def testaddunittestdomain(self):
        self.noouttest(["add", "domain", "--domain", "unittest"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "unittest")))

    def testverifyaddunittestdomain(self):
        command = "show domain --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: unittest", command)

    def testaddchangetest1domain(self):
        self.noouttest(["add", "domain", "--domain", "changetest1"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest1")))

    def testverifyaddchangetest1domain(self):
        command = "show domain --domain changetest1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetest1", command)

    def testaddchangetest2domain(self):
        self.noouttest(["add", "domain", "--domain", "changetest2"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest2")))

    def testverifyaddchangetest2domain(self):
        command = "show domain --domain changetest2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetest2", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

