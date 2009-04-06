#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del host command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelHost(TestBrokerCommand):

    def testdelunittest02(self):
        command = "del host --hostname unittest02.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest00(self):
        command = "del host --hostname unittest00.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest01(self):
        command = "del host --hostname unittest01.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest01(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest12(self):
        command = "del host --hostname unittest12.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest12(self):
        command = "show host --hostname unittest12.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelaurorawithnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_with_node
        self.noouttest(command.split(" "))

    def testverifydelaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        self.notfoundtest(command.split(" "))

    def testdelaurorawithoutnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_without_node
        self.noouttest(command.split(" "))

    def testverifydelaurorawithoutnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        self.notfoundtest(command.split(" "))

    def testdelnyaqd1(self):
        command = "del host --hostname nyaqd1.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest15(self):
        command = "del host --hostname unittest15.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest16(self):
        command = "del host --hostname unittest16.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest17(self):
        command = "del host --hostname unittest17.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest17(self):
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelhprackhosts(self):
        servers = 0
        for i in range(51, 100):
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            command = ["del", "host", "--hostname", hostname]
            self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

