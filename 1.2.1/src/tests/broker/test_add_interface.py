#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
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
            "--machine", "ut3c5n10", "--mac", self.hostmac0.upper(),
            "--ip", self.hostip0])

    def testaddut3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "ut3c5n10", "--mac", self.hostmac1.lower()])

    def testverifyaddut3c5n10interfaces(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s %s boot=True" %
                (self.hostmac0.lower(), self.hostip0), command)
        self.matchoutput(out, "Interface: eth1 %s 0.0.0.0 boot=False" %
                (self.hostmac1.lower()), command)

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
            "--machine", "ut3c1n3", "--mac", self.hostmac2.upper(),
            "--ip", self.hostip2])

    def testaddut3c1n3eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "ut3c1n3", "--mac", self.hostmac3.upper()])

    def testverifyaddut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 %s %s boot=True" %
                (self.hostmac2.lower(), self.hostip2), command)
        self.matchoutput(out, "Interface: eth1 %s 0.0.0.0 boot=False" %
                (self.hostmac3.lower()), command)

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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

