#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del interface command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelInterface(TestBrokerCommand):

    # Not testing del interface for np3c5n10... testing that those
    # interfaces are removed automatically when the machine is removed.

    # FIXME: Need a test for deleting by IP.
    def testdelnp3c1n3eth0(self):
        self.noouttest(["del", "interface", "--interface", "eth0",
            "--machine", "np3c1n3"])

    def testdelnp3c1n3eth1(self):
        self.noouttest(["del", "interface", "--mac", "00:11:25:4a:1a:35"])

    def testverifydelnp3c1n3interfaces(self):
        command = "show machine --machine np3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth", command)

    def testverifycatnp3c1n3interfaces(self):
        command = "cat --machine np3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out,
                """"cards/nic/eth0/hwdelr" = "00:11:25:4A:1A:34";""",
                command)
        self.matchclean(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchclean(out,
                """"cards/nic/eth1/hwdelr" = "00:11:25:4A:1A:35";""",
                command)
        self.matchclean(out,
                """"cards/nic/eth1/boot" = true;""",
                command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

