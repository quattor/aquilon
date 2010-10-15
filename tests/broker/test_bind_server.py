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
"""Module for testing the bind server command.

Note: This runs after make_aquilon and reconfigure tests.  If server
bindings are needed *before* those tests, they need to be in with
the TestPrebindServer tests.

"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

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
        self.matchclean(out, "'server_ips'", command)

    def testverifybindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)

    def testverifybindutsi1proto(self):
        command = "show service --service utsvc --instance utsi1 --format proto"
        out = self.commandtest(command.split(" "))
        msg = self.parse_service_msg(out, 1)
        svc = msg.services[0]
        self.failUnlessEqual(svc.name, "utsvc",
                             "Service name mismatch: %s instead of utsvc\n" %
                             svc.name)
        si = svc.serviceinstances[0]
        self.failUnlessEqual(si.name, "utsi1",
                             "Service name mismatch: %s instead of utsi1\n" %
                             si.name)
        # Using set() to avoid ordering issues
        servers = set([srv.fqdn for srv in si.servers])
        expected = set(["unittest00.one-nyp.ms.com",
                        "unittest02.one-nyp.ms.com"])
        self.failUnlessEqual(servers, expected,
                             "Wrong list of servers for service utsvc "
                             "instance utsi1: %s\n" %
                             " ".join(list(servers)))

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
        self.matchclean(out, "'server_ips'", command)

    def testreconfigureunittest00(self):
        command = "reconfigure --hostname unittest00.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

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

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template unittest00.one-nyp.ms.com",
                         command)
        self.matchoutput(out,
                         "include { 'service/utsvc/utsi1/server/config' };",
                         command)
        self.matchoutput(out,
                         "include { 'service/utsvc/utsi2/server/config' };",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)

