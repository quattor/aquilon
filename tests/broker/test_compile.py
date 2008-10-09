#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the compile command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestCompile(TestBrokerCommand):

    def testaddchange(self):
        # The plenary template should still be valid, but this
        # changes the dependencies to trigger a compile.
        sitedir = os.path.join(self.scratchdir, "unittest", "service",
                "utsvc", "utsi1", "client")
        self.gitcommand(["rm", "config.tpl"], cwd=sitedir)
        self.gitcommand(["commit", "-a", "-m",
                "removed unit test service instance 1"],
                cwd=os.path.join(self.scratchdir, "unittest"))
        self.ignoreoutputtest(["put", "--domain", "unittest"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testcompileunittest(self):
        command = "compile --domain unittest"
        out = self.commandtest(command.split(" "))
        # This could be more intelligent, maybe check that >= 2
        # hosts are being recompiled.
        self.matchoutput(out, "Cleaning old XML dependencies", command)
        self.matchoutput(out, "Updating XML dependencies", command)
        self.matchoutput(out, "Updating makefile dependencies", command)
        self.matchoutput(out, "Updating host XML configs", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompile)
    unittest.TextTestRunner(verbosity=2).run(suite)

