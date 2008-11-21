#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
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

    # Not testing del interface for ut3c5n10... testing that those
    # interfaces are removed automatically when the machine is removed.

    # FIXME: Need a test for deleting by IP.
    def testdelut3c1n3eth0(self):
        self.noouttest(["del", "interface", "--interface", "eth0",
            "--machine", "ut3c1n3"])

    def testdelut3c1n3eth1(self):
        self.noouttest(["del", "interface", "--mac", self.hostmac3.upper()])

    def testverifydelut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth", command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out,
                """"cards/nic/eth0/hwdelr" = "%s";""" % self.hostmac2.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth0/boot" = true;""",
                command)
        self.matchclean(out,
                """"cards/nic/eth1/hwdelr" = "%s";""" % self.hostmac3.upper(),
                command)
        self.matchclean(out,
                """"cards/nic/eth1/boot" = true;""",
                command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

