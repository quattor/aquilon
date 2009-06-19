#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelHost(TestBrokerCommand):

    def testdelunittest02(self):
        command = "del host --hostname unittest02.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest00(self):
        command = "del host --hostname unittest00.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest01(self):
        command = "del host --hostname unittest01.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest01(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest12(self):
        command = "del host --hostname unittest12.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest12(self):
        command = "show host --hostname unittest12.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelaurorawithnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_with_node
        self.noouttest(command.split(" "))

    def testverifydelaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        self.notfoundtest(command.split(" "))

    def testdelaurorawithoutnode(self):
        command = "del host --hostname %s.ms.com" % self.aurora_without_node
        self.noouttest(command.split(" "))

    def testverifydelaurorawithoutnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        self.notfoundtest(command.split(" "))

    def testdelnyaqd1(self):
        command = "del host --hostname nyaqd1.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest15(self):
        command = "del host --hostname unittest15.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest16(self):
        command = "del host --hostname unittest16.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest17(self):
        command = "del host --hostname unittest17.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelunittest17(self):
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
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
            self.noouttest(command)

    def testdelverarirackhosts(self):
        servers = 0
        for i in range(101, 110):
            hostname = "evh%d.aqd-unittest.ms.com" % (i - 100)
            command = ["del", "host", "--hostname", hostname]
            self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

