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
"""Module for testing the del host command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelHost(TestBrokerCommand):

    def testdelunittest02(self):
        command = "del host --hostname unittest02.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest00(self):
        command = "del host --hostname unittest00.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest01(self):
        command = "del host --hostname unittest01.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest01(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest12(self):
        command = "del host --hostname unittest12.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest12(self):
        command = "show host --hostname unittest12.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelaurorawithnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_with_node
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        self.notfoundtest(command.split(" "))

    def testdelaurorawithoutnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_without_node
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

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
        command = "del host --hostname unittest15.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest16(self):
        command = "del host --hostname unittest16.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest17(self):
        command = "del host --hostname unittest17.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifydelunittest17(self):
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest18(self):
        command = "del host --hostname unittest18.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testdeltest_aurora_default_os(self):
        command = "del host --hostname test_aurora_default_os.ms.com --quiet"
        self.noouttest(command.split(" "))

    def testverifydeltest_aurora_default_os(self):
        command = "show host --hostname test_aurora_default_os.ms.com"
        self.notfoundtest(command.split(" "))

    def testdeltest_windows_default_os(self):
        command = "del host --hostname test_windows_default_os.msad.ms.com --quiet"
        self.noouttest(command.split(" "))

    def testverifydeltest_windows_default_os(self):
        command = "show host --hostname test_windows_default_os.msad.ms.com"
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
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)

    def testdelverarirackhosts(self):
        servers = 0
        for i in range(101, 110):
            hostname = "evh%d.aqd-unittest.ms.com" % (i - 100)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)

    def testdel10gigrackhosts(self):
        for i in range(1, 25):
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)

    def testdelhaclusterhosts(self):
        for i in range(25, 49):
            port = i - 24
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)

            hostname = "evh%d.one-nyp.ms.com" % (i + 50)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
