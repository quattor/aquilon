#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

SRV_MSG = "WARNING: Server %s, is the last server bound to Service %s which still has clients"
SRVINST_MSG = "WARNING: Server %s, is the last server bound to Service %s, instance %s which still has clients"

class TestUnbindServer(TestBrokerCommand):

    def testunbindutsi1unittest02(self):
        command = ["unbind", "server",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRV_MSG % ("unittest02.one-nyp.ms.com","utsvc"),
                         command)

    def testunbinddns(self):
        self.noouttest(["unbind", "server",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--service", "dns", "--all"])
        command = ["unbind", "server",
                   "--hostname", "nyaqd1.ms.com",
                   "--service", "dns", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRV_MSG % ("nyaqd1.ms.com","dns"),
                         command)

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
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testverifybindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

    def testunbindutsi2unittest00(self):
        command = ["unbind", "server",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRVINST_MSG % ("unittest00.one-nyp.ms.com","utsvc","utsi2"),
                         command)

    def testverifycatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testverifybindutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

    def testunbindntp(self):
        command = ["unbind", "server",
                   "--hostname", "nyaqd1.ms.com", "--service", "ntp", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRV_MSG % ("nyaqd1.ms.com","ntp"),
                         command)

    def testverifyunbindntp(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: nyaqd1.ms.com", command)


    def testunbindaqd(self):
        command = ["unbind", "server",
                   "--hostname", "nyaqd1.ms.com", "--service", "aqd", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRV_MSG % ("nyaqd1.ms.com","aqd"),
                         command)

    def testverifyunbindaqd(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: nyaqd1.ms.com", command)

    def testunbindlemon(self):
        command = ["unbind", "server", "--hostname", "nyaqd1.ms.com",
                   "--service", "lemon", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRV_MSG % ("nyaqd1.ms.com","lemon"),
                         command)

    def testverifyunbindlemon(self):
        command = "show service --service lemon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: nyaqd1.ms.com", command)

    def testunbindsyslogng(self):
        command = ["unbind", "server", "--hostname", "nyaqd1.ms.com",
                   "--service", "syslogng", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err, SRV_MSG % ("nyaqd1.ms.com", "syslogng"),
                         command)

    def testverifyunbindsyslogng(self):
        command = "show service --service syslogng"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Server: nyaqd1.ms.com", command)

    def testunbindbootserver(self):
        command = ["unbind_server",
                   "--hostname=server9.aqd-unittest.ms.com",
                   "--service=bootserver", "--all"]

        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)

        self.matchoutput(err,
                         SRV_MSG % ("server9.aqd-unittest.ms.com","bootserver"),
                         command)

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
                command = ["unbind", "server", "--hostname", server,
                           "--service", service, "--instance", instance]
                (out, err) = self.successtest(command)
                self.assertEmptyOut(out, command)

    def testunbindpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.successtest(["unbind", "server", "--hostname", "nyaqd1.ms.com",
                          "--service", service, "--instance", "unittest"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
