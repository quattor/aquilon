#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del os command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelOS(TestBrokerCommand):

    def testdelutos(self):
        command = ["del_os", "--archetype=utarchetype1",
                   "--os=utos", "--vers=1.0"]
        self.noouttest(command)

    def testdelinvalid(self):
        command = ["del_os", "--archetype=utarchetype1",
                   "--os=os-does-not-exist", "--vers=1.0"]
        self.notfoundtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelOS)
    unittest.TextTestRunner(verbosity=2).run(suite)

