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
"""Module for testing the del host command."""

import unittest
import socket

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelHost(TestBrokerCommand):

    def testdelunittest02(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[11])
        command = "del host --hostname unittest02.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest00(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[2])
        command = "del host --hostname unittest00.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifydelunittest00dns(self):
        command = "show address --fqdn unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifyut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        # The primary name must be gone
        self.matchclean(out, "Primary Name:", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)
        # No interface should have the IP address
        self.matchclean(out, "Auxiliary:", command)
        self.matchclean(out, "Provides:", command)
        self.matchclean(out, str(self.net.unknown[0].usable[2]), command)

    # unittest01.one-nyp.ms.com gets deleted in test_del_windows_host.

    def testdelunittest12(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[7])
        command = "del host --hostname unittest12.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest12(self):
        command = "show host --hostname unittest12.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest20(self):
        self.dsdb_expect_delete(self.net.unknown[13].usable[2])
        command = "del host --hostname unittest20.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelunittest21(self):
        self.dsdb_expect_delete(self.net.unknown[11].usable[1])
        command = "del host --hostname unittest21.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelunittest22(self):
        self.dsdb_expect_delete(self.net.unknown[11].usable[2])
        command = "del host --hostname unittest22.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelunittest23(self):
        self.dsdb_expect_delete(self.net.vpls[0].usable[1])
        command = "del host --hostname unittest23.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelunittest24(self):
        self.dsdb_expect_delete(self.net.vpls[0].usable[2])
        command = "del host --hostname unittest24.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelunittest25(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[20])
        command = "del host --hostname unittest25.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelunittest26(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[23])
        command = "del host --hostname unittest26.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelaurorawithnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_with_node
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_with_node,
                         command)

    def testverifydelaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        self.notfoundtest(command.split(" "))

    def testdelaurorawithoutnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_without_node
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_without_node,
                         command)

    def testverifydelaurorawithoutnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        self.notfoundtest(command.split(" "))

    def testdelnyaqd1(self):
        command = "del host --hostname nyaqd1.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelnyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest15(self):
        self.dsdb_expect_delete(self.net.tor_net[0].usable[1])
        command = "del host --hostname unittest15.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest16(self):
        self.dsdb_expect_delete(self.net.tor_net[0].usable[2])
        command = "del host --hostname unittest16.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest17(self):
        self.dsdb_expect_delete(self.net.tor_net[0].usable[3])
        command = "del host --hostname unittest17.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest17(self):
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest18(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[18])
        command = "del host --hostname unittest18.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdeltest_aurora_default_os(self):
        command = "del host --hostname test-aurora-default-os.ms.com --quiet"
        self.noouttest(command.split(" "))

    def testverifydeltest_aurora_default_os(self):
        command = "show host --hostname test-aurora-default-os.ms.com"
        self.notfoundtest(command.split(" "))

    def testdeltest_windows_default_os(self):
        ip = self.net.tor_net[10].usable[-2]
        self.dsdb_expect_delete(ip)
        command = "del host --hostname test-windows-default-os.msad.ms.com --quiet"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydeltest_windows_default_os(self):
        command = "show host --hostname test-windows-default-os.msad.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelhprackhosts(self):
        servers = 0
        for i in range(51, 100):
            self.dsdb_expect_delete(self.net.tor_net[1].usable[i - 50])
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelverarirackhosts(self):
        servers = 0
        for i in range(101, 110):
            self.dsdb_expect_delete(self.net.tor_net[2].usable[i - 100])
            hostname = "evh%d.aqd-unittest.ms.com" % (i - 100)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdel10gigrackhosts(self):
        for i in range(1, 25):
            self.dsdb_expect_delete(self.net.tor_net2[2].usable[i + 1])
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdel_esx_bcp_clusterhosts(self):
        for i in range(25, 49):
            port = i - 24
            self.dsdb_expect_delete(self.net.tor_net2[3].usable[port])
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)

            self.dsdb_expect_delete(self.net.tor_net2[4].usable[port])
            hostname = "evh%d.one-nyp.ms.com" % (i + 50)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdeljack(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[17])
        command = "del host --hostname jack.cards.example.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()
        command = "show host --hostname jack.cards.example.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelfiler(self):
        self.dsdb_expect_delete(self.net.vm_storage_net[0].usable[25])
        command = "del host --hostname filer1.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()
        command = "show host --hostname filer1.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnotify(self):
        hostname = socket.getfqdn()
        self.noouttest(["unbind", "server", "--service", "utnotify",
                        "--instance", "localhost", "--hostname", hostname])

        self.dsdb_expect_delete("127.0.0.1")
        command = ["del", "host", "--hostname", hostname]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "sent 0 server notifications", command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
