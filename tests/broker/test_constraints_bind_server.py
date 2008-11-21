#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints involving the bind server command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestBindServerConstraints(TestBrokerCommand):

    # Test that unittest00 comes out of utsi1 but stays in utsi2
    def testunbindutsi1unittest00(self):
        self.noouttest(["unbind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    def testverifycatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi1';", command)
        self.matchoutput(out, "'servers' = list('unittest02.one-nyp.ms.com');", command)

    def testverifyunbindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

    def testverifycatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi2';", command)
        self.matchoutput(out, "'servers' = list('unittest00.one-nyp.ms.com');", command)

    def testverifyutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)

    def testrejectdelserviceinstance(self):
        command = "del service --service utsvc --instance utsi2"
        self.badrequesttest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)

