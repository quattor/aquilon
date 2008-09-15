#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddService(TestBrokerCommand):

    def testaddafsinstance(self):
        command = "add service --service afs --instance q.ny.ms.com"
        self.noouttest(command.split(" "))

    def testverifyaddafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)

    def testaddextraafsinstance(self):
        command = "add service --service afs --instance q.ln.ms.com"
        self.noouttest(command.split(" "))

    def testverifyaddextraafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ln.ms.com", command)

    def testaddbootserverinstance(self):
        command = "add service --service bootserver --instance np.test"
        self.noouttest(command.split(" "))

    def testverifyaddbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)

    def testadddnsinstance(self):
        command = "add service --service dns --instance nyinfratest"
        self.noouttest(command.split(" "))

    def testverifyadddnsinstance(self):
        command = "show service --service dns"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: dns Instance: nyinfratest", command)

    def testaddntpinstance(self):
        command = "add service --service ntp --instance pa.ny.na"
        self.noouttest(command.split(" "))

    def testverifyaddntpinstance(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: ntp Instance: pa.ny.na", command)

    def testaddaqdinstance(self):
        command = "add service --service aqd --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifyaddntpinstance(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)

    def testaddutsi1instance(self):
        command = "add service --service utsvc --instance utsi1"
        self.noouttest(command.split(" "))

    def testcatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi1';", command)
        self.matchoutput(out, "'servers' = list();", command)

    def testcatutsi1default(self):
        command = "cat --service utsvc --instance utsi1 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi1/client/config;",
                         command)
        self.matchoutput(out,
                         "'/system/services/utsvc' = create('servicedata/utsvc/utsi1/config');",
                         command)
        self.matchoutput(out, "include { 'service/utsvc/client/config' };",
                         command)

    def testaddutsi2instance(self):
        command = "add service --service utsvc --instance utsi2"
        self.noouttest(command.split(" "))

    def testcatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi2';", command)
        self.matchoutput(out, "'servers' = list();", command)

    def testcatutsi2default(self):
        command = "cat --service utsvc --instance utsi2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi2/client/config;",
                         command)
        self.matchoutput(out,
                         "'/system/services/utsvc' = create('servicedata/utsvc/utsi2/config');",
                         command)
        self.matchoutput(out, "include { 'service/utsvc/client/config' };",
                         command)

    def testcatutsvc(self):
        command = "cat --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc/config;",
                         command)

    def testcatutsvcdefault(self):
        command = "cat --service utsvc --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/client/config;", command)

    def testverifyaddutsvcinstances(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)

    def testaddutsvc2(self):
        command = "add service --service utsvc2"
        self.noouttest(command.split(" "))

    def testcatutsvc2(self):
        command = "cat --service utsvc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc2/config;",
                         command)

    def testcatutsvc2default(self):
        command = "cat --service utsvc2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc2/client/config;",
                         command)

    def testverifyutsvc2(self):
        command = "show service --service utsvc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc2", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddService)
    unittest.TextTestRunner(verbosity=2).run(suite)

