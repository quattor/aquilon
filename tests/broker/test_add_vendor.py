#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add vendor command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddVendor(TestBrokerCommand):

    def testaddexisting(self):
        command = "add vendor --vendor intel"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "vendor 'intel' already exists", command)

    def testaddbadname(self):
        command = "add vendor --vendor oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "vendor name 'oops@!' is not valid", command)

    def testaddutvendor(self):
        command = "add vendor --vendor utvendor"
        self.noouttest(command.split(" "))

    def testverifyutvendor(self):
        command = "show vendor --vendor utvendor"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor", command)

    def testverifyutvendorall(self):
        command = "show vendor --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor", command)
        self.matchoutput(out, "Vendor: intel", command)

    def testnotfoundvendor(self):
        command = "show vendor --vendor vendor-does-not-exist"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVendor)
    unittest.TextTestRunner(verbosity=2).run(suite)

