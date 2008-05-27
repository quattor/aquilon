#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the manage command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestManage(TestBrokerCommand):

    def testmanageaquilon02(self):
        self.noouttest(["manage", "--hostname", "aquilon02.one-nyp.ms.com",
            "--domain", "changetest1"])

    def testverifymanageaquilon02(self):
        command = "show host --hostname aquilon02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: aquilon02.one-nyp.ms.com", command)
        self.matchoutput(out, "Domain: changetest1", command)

    def testmanageaquilon00(self):
        self.noouttest(["manage", "--hostname", "aquilon00.one-nyp.ms.com",
            "--domain", "changetest2"])

    def testverifymanageaquilon00(self):
        command = "show host --hostname aquilon00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: aquilon00.one-nyp.ms.com", command)
        self.matchoutput(out, "Domain: changetest2", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

