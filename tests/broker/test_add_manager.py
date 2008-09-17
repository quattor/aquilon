#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add manager command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddManager(TestBrokerCommand):

    # Note: If changing this, also change testverifyshowmissingmanager
    # in test_add_aquilon_host.py.
    def testaddunittest00r(self):
        self.noouttest(["add", "manager", "--ip", self.hostip10,
            "--hostname", "unittest00.one-nyp.ms.com"])

    def testverifyaddunittest00r(self):
        command = "show manager --manager unittest00r.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Manager: unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip10, command)
        self.matchoutput(out, "MAC: %s" % self.hostmac10, command)
        self.matchoutput(out, "Interface: bmc %s boot=False" % self.hostmac10,
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testaddunittest02rsa(self):
        self.noouttest(["add", "manager", "--ip", self.hostip11,
            "--hostname", "unittest02.one-nyp.ms.com",
            "--manager", "unittest02rsa.one-nyp.ms.com",
            "--interface", "ilo", "--mac", self.hostmac11])

    def testverifyaddunittest02rsa(self):
        command = "show manager --manager unittest02rsa.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Manager: unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip11, command)
        self.matchoutput(out, "MAC: %s" % self.hostmac11, command)
        self.matchoutput(out, "Interface: ilo %s boot=False" % self.hostmac11,
                         command)
        self.matchoutput(out, "Blade: ut3c5n10", command)



if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddManager)
    unittest.TextTestRunner(verbosity=2).run(suite)

