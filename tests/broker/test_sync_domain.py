#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the sync domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestSyncDomain(TestBrokerCommand):

    def testprepchangetest2domain(self):
        self.gitcommand(["checkout", "master"],
                cwd=os.path.join(self.scratchdir, "changetest2"))

    def testsyncchangetest2domain(self):
        self.ignoreoutputtest(["sync", "--domain", "changetest2"],
                cwd=os.path.join(self.scratchdir, "changetest2"))
        template = os.path.join(self.scratchdir, "changetest2", "aquilon",
                "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        self.assertEqual(contents[-1], "#Added by unittest\n")


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSyncDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

