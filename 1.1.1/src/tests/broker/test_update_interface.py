#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the update interface command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUpdateInterface(TestBrokerCommand):

    def testupdateut3c5n10eth0mac(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
            "--machine", "ut3c5n10", "--mac", "00:00:00:00:00:4E"])

    def testupdateut3c5n10eth0ip(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
            "--machine", "ut3c5n10", "--ip", "8.8.5.14"])

    def testupdateut3c5n10eth1(self):
        self.noouttest(["update", "interface", "--interface", "eth1",
            "--machine", "ut3c5n10", "--mac", "00:00:00:00:00:50",
            "--ip", "8.8.5.15", "--boot"])

    def testupdateut3c5n10eth2(self):
        self.badrequesttest(["update", "interface", "--interface", "eth2",
            "--machine", "ut3c5n10", "--boot"])

    def testverifyupdateut3c5n10interfaces(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 00:00:00:00:00:4E 8.8.5.14 boot=False", command)
        self.matchoutput(out, "Interface: eth1 00:00:00:00:00:50 8.8.5.15 boot=True", command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "00:00:00:00:00:4E";""",
                command)
        self.matchclean(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "00:00:00:00:00:50";""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/boot" = true;""",
                command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

