#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the rebind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestRebindClient(TestBrokerCommand):

    def testrebindafs(self):
        command = ["rebind", "client",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "afs", "--instance", "q.ln.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service afs instance q.ln.ms.com",
                         command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com removing binding for "
                         "service afs instance q.ny.ms.com",
                         command)

    def testverifyrebindafs(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ln.ms.com", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)

