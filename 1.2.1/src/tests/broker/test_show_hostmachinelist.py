#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the show hostmachinelist command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowHostMachineList(TestBrokerCommand):

    def testshowhostmachinelist(self):
        command = "show hostmachinelist"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com,ut3c1n3", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com,ut3c5n10", command)

    def testshowhostmachinelistarchetype(self):
        command = "show hostmachinelist --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com,ut3c1n3", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com,ut3c5n10", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowHostMachineList)
    unittest.TextTestRunner(verbosity=2).run(suite)

