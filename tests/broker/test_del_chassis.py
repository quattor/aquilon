#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del chassis command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelChassis(TestBrokerCommand):

    def testdelut3c5(self):
        command = "del chassis --chassis ut3c5.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut3c5(self):
        command = "show chassis --chassis ut3c5.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut3c1(self):
        command = "del chassis --chassis ut3c1.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut3c1(self):
        command = "show chassis --chassis ut3c1.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut9chassis(self):
        for i in range(1, 6):
            command = "del chassis --chassis ut9c%d.aqd-unittest.ms.com" % i
            self.noouttest(command.split(" "))

    def testverifydelut9chassis(self):
        for i in range(1, 6):
            command = "show chassis --chassis ut9c%d.aqd-unittest.ms.com" % i
            self.notfoundtest(command.split(" "))


if __name__=='__main__':
    import aquilon.aqdb.depends
    import nose

    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelChassis)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()
