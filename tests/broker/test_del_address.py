#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the del address command."""


import os
import sys
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from ipaddr import IPv4Address
from brokertest import TestBrokerCommand


class TestDelAddress(TestBrokerCommand):

    def testbasic(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[13])
        command = ["del_address", "--ip=%s" % self.net.unknown[0].usable[13]]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifybasic(self):
        command = ["show_address", "--fqdn=arecord13.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def testdefaultenv(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[14])
        default = self.config.get("site", "default_dns_environment")
        command = ["del_address", "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", default]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifydefaultenv(self):
        command = ["show_address", "--fqdn=arecord14.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def testutenvenv(self):
        command = ["del_address", "--ip", self.net.unknown[1].usable[14],
                   "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        self.noouttest(command)

    def testverifyutenvenv(self):
        command = ["show_address", "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        self.notfoundtest(command)

    def testbadip(self):
        ip = self.net.unknown[0].usable[14]
        command = ["del_address", "--ip", ip,
                   "--fqdn=arecord15.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Record arecord15.aqd-unittest.ms.com, ip "
                         "%s not found." % ip, command)

    def testcleanup(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[15])
        command = ["del_address", "--ip=%s" % self.net.unknown[0].usable[15],
                   "--fqdn=arecord15.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testfailbadenv(self):
        default = self.config.get("site", "default_dns_environment")
        command = ["del_address", "--ip=%s" % self.net.unknown[0].usable[15],
                   "--fqdn=arecord15.aqd-unittest.ms.com",
                   "--dns_environment=environment-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DNS Environment environment-does-not-exist not found.",
                         command)

    def testfailprimary(self):
        ip = self.net.unknown[0].usable[2]
        command = ["del", "address", "--ip", ip, "--fqdn",
                   "unittest00.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record unittest00.one-nyp.ms.com [%s] is the "
                         "primary name of machine unittest00.one-nyp.ms.com, "
                         "therefore it cannot be deleted." % ip,
                         command)

    def testfailipinuse(self):
        ip = self.net.unknown[0].usable[3]
        command = ["del", "address", "--ip", ip, "--fqdn",
                   "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is still in use by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com" % ip,
                         command)

    def testdelunittest20_e1(self):
        ip = self.net.unknown[12].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "address", "--ip", ip,
                   "--fqdn", "unittest20-e1.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelzebra3(self):
        ip = self.net.unknown[13].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "address", "--ip", ip,
                   "--fqdn", "zebra3.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
