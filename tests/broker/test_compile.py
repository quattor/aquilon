#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
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

    def test_000_precompile(self):
        # Before the tests below, make sure everything is up to date.
        command = "compile --domain unittest"
        out = self.commandtest(command.split(" "))

    def test_100_addchange(self):
        # Change the template used by utsi1 clients to trigger a recompile.
        templatedir = os.path.join(self.scratchdir, "unittest")
        template = os.path.join(templatedir, "service", "utsvc", "utsi1",
                                "client", "config.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest broker/test_compile\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m",
                         "modified unit test service instance 1"],
                         cwd=templatedir)
        self.ignoreoutputtest(["put", "--domain", "unittest"],
                              env=self.gitenv(), cwd=templatedir)

    def test_200_compileunittest(self):
        command = "compile --domain unittest"
        out = self.commandtest(command.split(" "))
        # Currently assumes that there is only one client of utsi1.
        # The idea is to check that only that hosts that needed to
        # be compiled actually were.
        self.matchoutput(out, "Updated 1 XML dependencies", command)
        self.matchoutput(out, "Updated 1 makefile dependencies", command)
        self.matchoutput(out, "Updated 1 host XML configs", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompile)
    unittest.TextTestRunner(verbosity=2).run(suite)

