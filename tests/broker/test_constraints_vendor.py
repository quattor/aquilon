#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints in commands involving vendor."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestVendorConstraints(TestBrokerCommand):

    def testdelvendorwithmodel(self):
        command = "del vendor --vendor hp"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "in use by a model", command)

    def testverifydelvendorwithmodel(self):
        command = ["show_vendor", "--vendor=hp"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: hp", command)

    def testdelvendorwithcpu(self):
        command = "del vendor --vendor intel"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "in use by a cpu", command)

    def testverifydelvendorwithcpu(self):
        command = ["show_vendor", "--vendor=intel"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: intel", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestVendorConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
