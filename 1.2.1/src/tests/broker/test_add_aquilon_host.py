#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add aquilon host command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddAquilonHost(TestBrokerCommand):

    def testaddunittest00(self):
        self.noouttest(["add", "aquilon", "host", "--status", "production",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--machine", "ut3c1n3", "--domain", "unittest"])

    def testverifyaddunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Blade: ut3c1n3", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Status: production", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAquilonHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

