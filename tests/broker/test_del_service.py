#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelService(TestBrokerCommand):

    def testdelafsinstance(self):
        command = "del service --service afs --instance q.ny.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: q.ny.ms.com", command)

    def testdelextraafsinstance(self):
        command = "del service --service afs --instance q.ln.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelextraafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: q.ln.ms.com", command)

    def testdelbootserverinstance(self):
        command = "del service --service bootserver --instance np.test"
        self.noouttest(command.split(" "))

    def testverifydelbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: bootserver Instance: np.test", command)

    def testdeldnsinstance(self):
        command = "del service --service dns --instance nyinfratest"
        self.noouttest(command.split(" "))

    def testverifydeldnsinstance(self):
        command = "show service --service dns"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: dns Instance: nyinfratest", command)

    def testdelntpinstance(self):
        command = "del service --service ntp --instance pa.ny.na"
        self.noouttest(command.split(" "))

    def testverifydelntpinstance(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: ntp Instance: pa.ny.na", command)

    def testdelutsi1instance(self):
        command = "del service --service utsvc --instance utsi1"
        self.noouttest(command.split(" "))

    def testdelutsi2instance(self):
        command = "del service --service utsvc --instance utsi2"
        self.noouttest(command.split(" "))

    def testverifydelutsvcinstance(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: utsvc Instance: utsi1", command)
        self.matchclean(out, "Service: utsvc Instance: utsi2", command)

    def testdelutsvc2(self):
        command = "del service --service utsvc2"
        self.noouttest(command.split(" "))

    def testverifydelutsvc2(self):
        command = "show service --service utsvc2"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelService)
    unittest.TextTestRunner(verbosity=2).run(suite)

