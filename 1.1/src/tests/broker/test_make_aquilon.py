#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the make aquilon command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMakeAquilon(TestBrokerCommand):

    def testmakeaquilon02(self):
        self.noouttest(["make", "aquilon",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--personality", "ms/fid/spg/ice", "--os", "linux/4.0.1-x86_64"])

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeAquilon)
    unittest.TextTestRunner(verbosity=2).run(suite)

