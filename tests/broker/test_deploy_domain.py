#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the deploy domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDeployDomain(TestBrokerCommand):

    def testdeploychangetest1domain(self):
        self.noouttest(["deploy", "--domain", "changetest1"])
        template = os.path.join(self.config.get("broker", "kingdir"),
                "aquilon", "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        self.assertEqual(contents[-1], "#Added by unittest\n")


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeployDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

