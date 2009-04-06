#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints involving the bind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestBindClientConstraints(TestBrokerCommand):

    def testrebindfails(self):
        command = ["bind", "client",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is already bound", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestBindClientConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
