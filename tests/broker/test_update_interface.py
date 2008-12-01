#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
            "--machine", "ut3c5n10", "--mac", self.hostmac6])

    def testupdateut3c5n10eth0ip(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
            "--machine", "ut3c5n10", "--ip", self.hostip6])

    def testupdateut3c5n10eth1(self):
        self.noouttest(["update", "interface", "--interface", "eth1",
            "--hostname", "unittest02.one-nyp.ms.com", "--mac", self.hostmac7,
            "--ip", self.hostip7, "--boot"])

    def testupdateut3c5n10eth2(self):
        self.badrequesttest(["update", "interface", "--interface", "eth2",
            "--machine", "ut3c5n10", "--boot"])

    def testverifyupdateut3c5n10interfaces(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        # FIXME: This is currently not working, command nees rethinking.
        #self.matchoutput(out, "IP: %s" % self.hostip7, command)
        self.matchoutput(out, "Interface: eth0 %s boot=False" %
                         self.hostmac6.lower(), command)
        self.matchoutput(out, "Interface: eth1 %s boot=True" %
                         self.hostmac7.lower(), command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "%s";""" % self.hostmac6.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "%s";""" % self.hostmac7.upper(),
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/boot" = true;""",
                command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

