#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the show hostiplist command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowHostIPList(TestBrokerCommand):

    def testshowhostiplist(self):
        command = "show hostiplist"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "aquilon02.one-nyp.ms.com,172.31.73.14", command)
        self.matchoutput(out, "aquilon00.one-nyp.ms.com,172.31.64.199", command)

    def testshowhostiplistarchetype(self):
        command = "show hostiplist --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "aquilon02.one-nyp.ms.com,172.31.73.14", command)
        self.matchoutput(out, "aquilon00.one-nyp.ms.com,172.31.64.199", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowHostIPList)
    unittest.TextTestRunner(verbosity=2).run(suite)

