#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelDomain(TestBrokerCommand):

    def testdelunittestdomain(self):
        command = "del domain --domain unittest"
        self.noouttest(command.split(" "))
        self.assert_(not os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "unittest")))

    def testverifydelunittestdomain(self):
        command = "show domain --domain unittest"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

