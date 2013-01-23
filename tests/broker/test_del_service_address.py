#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012  Contributor
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
"""Module for testing the del service address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelServiceAddress(TestBrokerCommand):

    def testdelzebra2(self):
        ip = self.net.unknown[13].usable[1]
        self.dsdb_expect_delete(ip)
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelzebra2again(self):
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service Address zebra2, hostresource instance "
                         "not found.", command)
        self.dsdb_verify(empty=True)

    def testverifyzebra2(self):
        command = ["show", "address", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Record zebra2.aqd-unittest.ms.com not "
                         "found.", command)

    def testdelzebra3(self):
        ip = self.net.unknown[13].usable[0]
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add("zebra3.aqd-unittest.ms.com", ip)
        command = ["del", "service", "address", "--keep_dns",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--name", "zebra3"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyzebra3(self):
        ip = self.net.unknown[13].usable[0]
        command = ["show", "address", "--fqdn", "zebra3.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: zebra3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "IP: %s" % ip, command)
        self.matchclean(out, "Assigned To", command)
        self.matchclean(out, "ut3c5n2", command)
        self.matchclean(out, "eth0", command)

    def testdelzebra3again(self):
        command = ["del", "service", "address", "--name", "zebra3",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service Address zebra3, hostresource instance "
                         "not found.", command)
        self.dsdb_verify(empty=True)

    def testfailhostname(self):
        command = ["del", "service", "address", "--name", "hostname",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The primary address of the host cannot be "
                         "deleted.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
