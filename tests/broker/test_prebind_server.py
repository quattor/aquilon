#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
""" This is needed to make sure that a server is bound to the aqd service
    before make aquilon runs."""


import socket
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPrebindServer(TestBrokerCommand):

    def testbindaqdserver(self):
        self.noouttest(["bind", "server",
            "--hostname", "nyaqd1.ms.com",
            "--service", "aqd", "--instance", "ny-prod"])

    def testverifybindaqd(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindlemonserver(self):
        self.noouttest(["bind", "server", "--hostname", "nyaqd1.ms.com",
                        "--service", "lemon", "--instance", "ny-prod"])

    def testverifybindlemon(self):
        command = "show service --service lemon --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindbootserver(self):
        self.noouttest(["bind_server",
                        "--hostname=server9.aqd-unittest.ms.com",
                        "--service=bootserver", "--instance=np.test"])

    def testverifybindbootserver(self):
        command = "show service --service bootserver --instance np.test"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: server9.aqd-unittest.ms.com", command)

    def testbindchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for (s, n) in [(1, 'a'), (2, 'b'), (3, 'c')]:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                server = "server%d.aqd-unittest.ms.com" % s
                instance = "ut.%s" % n
                self.noouttest(["bind", "server", "--hostname", server,
                                "--service", service, "--instance", instance])

    def testbinddns(self):
        self.noouttest(["bind", "server",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--service", "dns", "--instance", "utdnsinstance"])
        self.noouttest(["bind", "server",
                        "--hostname", "nyaqd1.ms.com",
                        "--service", "dns", "--instance", "utdnsinstance"])

    def testcatdns(self):
        command = "cat --service dns --instance utdnsinstance"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"servers" = list\(\s*"nyaqd1.ms.com",\s*'
                          r'"unittest02.one-nyp.ms.com"\s*\);',
                          command)
        # Relying on 'nyaqd1.ms.com' to be in DNS isn't going to work
        # in other locations.  A better choice might be one of the
        # root servers (a.root-servers.net) but there's no sane way
        # to add that to the database right now.  Maybe post DNS
        # revamp.
        self.searchoutput(out,
                          '"server_ips" = list\(\s*"%s",\s*"%s"\s*\);' %
                          (socket.gethostbyname('nyaqd1.ms.com'),
                           self.net.unknown[0].usable[0]),
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPrebindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
