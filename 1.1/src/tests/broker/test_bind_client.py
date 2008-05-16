#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the bind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestBindClient(TestBrokerCommand):

    def testbindafs(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "afs", "--instance", "q.ny.ms.com"])

    def testbinddns(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "dns", "--instance", "nyinfratest"])

    def testbindbootserver(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "bootserver", "--instance", "np.test"])

    def testbindntp(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "ntp", "--instance", "pa.ny.na"])

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)

