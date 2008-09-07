#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add interface command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddInterface(TestBrokerCommand):

    def testaddut3c5n10eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3c5n10", "--mac", self.hostmac0.upper()])

    def testaddut3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "ut3c5n10", "--mac", self.hostmac1.lower()])

    def testverifyaddut3c5n10interfaces(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                self.hostmac0.lower(), command)
        self.matchoutput(out, "Interface: eth1 %s boot=False" %
                self.hostmac1.lower(), command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac0.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "%s";""" % self.hostmac1.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth1/boot" = true;""",
                command)

    def testaddut3c1n3eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3c1n3", "--mac", self.hostmac2.upper()])

    def testaddut3c1n3eth1(self):
        # FIXME: This used to add self.hostip3
        testmac = []
        for i in self.hostmac3.split(":"):
            if i.startswith("0"):
                testmac.append(i[1])
            else:
                testmac.append(i)
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "ut3c1n3", "--mac", ":".join(testmac)])

    def testverifyaddut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac2.lower(), command)
        self.matchoutput(out, "Interface: eth1 %s boot=False" %
                         self.hostmac3.lower(), command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac2.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "%s";""" % self.hostmac3.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth1/boot" = true;""",
                command)

    def testaddut3c1n4eth0(self):
        testmac = "".join(self.hostmac4.split(":"))
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "ut3c1n4", "--mac", testmac])

    def testverifyaddut3c1n4interface(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac4.lower(), command)

    def testverifycatut3c1n4interface(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac4.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)

    # FIXME: This test might need to move elsewhere...
    #def testrejectut3c1n4eth1(self):
        # This is an old (relatively) well known DNS server sitting out
        # on the net that will probably never be controlled by the Firm.
        # It should not appear in our network table, and thus should
        # trigger a bad request here.
    #    self.badrequesttest(["add", "interface", "--interface", "eth1",
    #        "--machine", "ut3c1n4", "--mac", "02:02:04:02:02:04",
    #        "--ip", "4.2.2.4"])

    #def testverifyrejectut3c1n4eth1(self):
    #    command = "show machine --machine ut3c1n4"
    #    out = self.commandtest(command.split(" "))
    #    self.matchclean(out, "Interface: eth1", command)

    # FIXME: This test might need to move elsewhere...
    #def testrejectsixthip(self):
        # This tests that the sixth ip offset on a tor_switch network
        # gets rejected.
        # FIXME: Hard-coded.  Assumes the 8.8.4.0 subnet, since all
        # the tests are using 8.8.[4567].* ips.
    #    self.badrequesttest(["add", "interface", "--interface", "eth2",
    #        "--machine", "ut3c1n4", "--mac", "02:02:08:08:04:06",
    #        "--ip", "8.8.4.6"])

    #def testverifyrejectsixthip(self):
    #    command = "show machine --machine ut3c1n4"
    #    out = self.commandtest(command.split(" "))
    #    self.matchclean(out, "Interface: eth2", command)

    # FIXME: This test might need to move elsewhere...
    #def testrejectseventhip(self):
        # This tests that the seventh ip offset on a tor_switch network
        # gets rejected.
        # FIXME: Hard-coded.  Assumes the 8.8.4.0 subnet, since all
        # the tests are using 8.8.[4567].* ips.
    #    self.badrequesttest(["add", "interface", "--interface", "eth3",
    #        "--machine", "ut3c1n4", "--mac", "02:02:08:08:04:07",
    #        "--ip", "8.8.4.7"])

    #def testverifyrejectseventhip(self):
    #    command = "show machine --machine ut3c1n4"
    #    out = self.commandtest(command.split(" "))
    #    self.matchclean(out, "Interface: eth3", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

