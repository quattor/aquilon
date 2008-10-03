#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del manager command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelManager(TestBrokerCommand):

    def testdelunittest00r(self):
        command = "del manager --manager unittest00r.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest00r(self):
        command = "show manager --manager unittest00r.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest02rsa(self):
        command = "del manager --manager unittest02rsa.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest02rsa(self):
        command = "show manager --manager unittest02rsa.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest12r(self):
        command = "del manager --manager unittest12r.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest12r(self):
        command = "show manager --manager unittest12r.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelManager)
    unittest.TextTestRunner(verbosity=2).run(suite)

