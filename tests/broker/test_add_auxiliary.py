#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add auxiliary command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddAuxiliary(TestBrokerCommand):

    def testaddunittest00e1(self):
        self.noouttest(["add", "auxiliary", "--ip", self.hostip3,
            "--auxiliary", "unittest00-e1.one-nyp.ms.com",
            "--machine", "ut3c1n3", "--interface", "eth1"])

    def testverifyaddunittest00e1(self):
        command = "show auxiliary --auxiliary unittest00-e1.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Auxiliary: unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip3, command)
        self.matchoutput(out, "MAC: %s" % self.hostmac3, command)
        self.matchoutput(out, "Interface: eth1 %s boot=False" % self.hostmac3,
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testrejectut3c1n4eth1(self):
        # This is an old (relatively) well known DNS server sitting out
        # on the net that will probably never be controlled by the Firm.
        # It should not appear in our network table, and thus should
        # trigger a bad request here.
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e1.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", "02:02:04:02:02:04",
            "--interface", "eth1", "--ip", "4.2.2.4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not determine network", command)

    def testverifyrejectut3c1n4eth1(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth1", command)

    def testrejectsixthip(self):
        # This tests that the sixth ip offset on a tor_switch network
        # gets rejected.
        # FIXME: Hard-coded.  Assumes the 8.8.4.0 subnet, since all
        # the tests are using 8.8.[4567].* ips.
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e1.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", "02:02:08:08:04:06",
            "--interface", "eth2", "--ip", "8.8.4.6"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "reserved for dynamic dhcp", command)

    def testverifyrejectsixthip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth2", command)

    def testrejectseventhip(self):
        # This tests that the seventh ip offset on a tor_switch network
        # gets rejected.
        # FIXME: Hard-coded.  Assumes the 8.8.4.0 subnet, since all
        # the tests are using 8.8.[4567].* ips.
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e1.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", "02:02:08:08:04:07",
            "--interface", "eth3", "--ip", "8.8.4.7"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "reserved for dynamic dhcp", command)

    def testverifyrejectseventhip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth3", command)

    def testrejectmacinuse(self):
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e4.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", self.hostmac4,
            "--interface", "eth4", "--ip", "8.8.4.7"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Mac '%s' already in use" % self.hostmac4,
                         command)

    def testverifyrejectseventhip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth4", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuxiliary)
    unittest.TextTestRunner(verbosity=2).run(suite)

