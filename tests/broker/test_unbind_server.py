#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the unbind server command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestUnbindServer(TestBrokerCommand):

    def testunbindutsi1unittest02(self):
        self.noouttest(["unbind", "server",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc", "--all"])

    # Should have already been unbound...
    # Hmm... this (as implemented) actually returns 0.  Kind of a pointless
    # test case, at least for now.
    #def testrejectunbindutsi1unittest00(self):
    #    self.badrequesttest(["unbind", "server",
    #        "--hostname", "unittest00.one-nyp.ms.com",
    #        "--service", "utsvc", "--instance", "utsi1"])

    def testverifycatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi1';", command)
        self.matchoutput(out, "'servers' = list();", command)

    def testverifybindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

    def testunbindutsi2unittest00(self):
        self.noouttest(["unbind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi2"])

    def testverifycatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi2';", command)
        self.matchoutput(out, "'servers' = list();", command)

    def testverifybindutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

    def testunbindaqd(self):
        self.noouttest(["unbind", "server",
            "--hostname", "nyaqd1.ms.com", "--service", "aqd", "--all"])

    def testverifyunbindaqd(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: nyaqd1.ms.com", command)

    def testunbindlemon(self):
        self.noouttest(["unbind", "server", "--hostname", "nyaqd1.ms.com",
                        "--service", "lemon", "--all"])

    def testverifyunbindlemon(self):
        command = "show service --service lemon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: nyaqd1.ms.com", command)

    def testunbindbootserver(self):
        self.noouttest(["unbind_server",
                        "--hostname=server9.aqd-unittest.ms.com",
                        "--service=bootserver", "--all"])

    def testverifyunbindbootserver(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: server9.aqd-unittest.ms.com", command)

    def testunbindchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for (s, n) in [(1, 'a'), (2, 'b'), (3, 'c')]:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                server = "server%d.aqd-unittest.ms.com" % s
                instance = "ut.%s" % n
                self.noouttest(["unbind", "server", "--hostname", server,
                                "--service", service, "--instance", instance])


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)

