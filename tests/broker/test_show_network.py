#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the show service --all command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowNetwork(TestBrokerCommand):

    def testshownetwork(self):
        # We're only showing the networks for a building because for global the test would fail!
        command = "show network --building np"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Network", command)
        self.matchoutput(out, "np06ba6s45_netapp", command)
        self.matchoutput(out, "10.184.78.224", command)
        self.matchoutput(out, "np.ny.na", command)

    def testshownetworkproto(self):
        command = "show network --building np --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_netlist_msg(out)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)

