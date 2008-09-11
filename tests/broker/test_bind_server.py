#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the bind server command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestBindServer(TestBrokerCommand):

    def testbindutsi1unittest02(self):
        self.noouttest(["bind", "server",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    # Test binding multiple servers to a single instance
    def testbindutsi1unittest00(self):
        self.noouttest(["bind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    def testcatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi1';", command)
        self.matchoutput(out, "'servers' = list('unittest00.one-nyp.ms.com', 'unittest02.one-nyp.ms.com');", command)

    def testverifybindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)

    # Test binding a server to multiple instances
    def testbindutsi2unittest00(self):
        self.noouttest(["bind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi2"])

    def testcatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi2';", command)
        self.matchoutput(out, "'servers' = list('unittest00.one-nyp.ms.com');", command)

    def testverifybindutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)

    def testverifyshowserviceserver(self):
        command = "show service --server unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)

    def testverifyshowserviceserviceserver(self):
        command = "show service --service utsvc --server unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)

