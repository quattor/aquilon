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

    def testaddnp3c5n10eth0(self):
        self.noouttest(["add", "interface", "--interface", "eth0",
            "--machine", "np3c5n10", "--mac", "00:14:5E:D7:7F:4E",
            "--ip", "172.31.73.14"])

    def testaddnp3c5n10eth1(self):
        self.noouttest(["add", "interface", "--interface", "eth1",
            "--machine", "np3c5n10", "--mac", "00:14:5E:D7:7F:50"])

    def testverifyaddnp3c5n10interfaces(self):
        command = "show machine --machine np3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Interface: eth0 00:14:5e:d7:7f:4e 172.31.73.14 boot=True", command)
        self.matchoutput(out, "Interface: eth1 00:14:5e:d7:7f:50 0.0.0.0 boot=False", command)

    def testverifycatnp3c5n10interfaces(self):
        command = "cat --machine np3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"cards/nic/eth0/hwaddr" = "00:14:5E:D7:7F:4E";""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchoutput(out,
                """"cards/nic/eth1/hwaddr" = "00:14:5E:D7:7F:50";""",
                command)
        self.assert_(out.find(""""cards/nic/eth1/boot" = true;""") < 0)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

