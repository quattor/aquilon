#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del vendor command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelVendor(TestBrokerCommand):

    def testdelinvalidvendor(self):
        command = ["del_vendor", "--vendor=vendor-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "No vendor with name 'vendor-does-not-exist'",
                         command)

    def testdelutvendor(self):
        command = ["del_vendor", "--vendor=utvendor"]
        self.noouttest(command)

    def testverifydelutvendor(self):
        command = ["show_vendor", "--vendor=utvendor"]
        self.notfoundtest(command)

    def testverifyall(self):
        command = ["show_vendor", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Vendor: utvendor", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVendor)
    unittest.TextTestRunner(verbosity=2).run(suite)

