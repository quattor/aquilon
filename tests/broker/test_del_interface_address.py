#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Module for testing the del interface address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelInterfaceAddress(TestBrokerCommand):

    def testdelkeepdns(self):
        ip = self.net.unknown[12].usable[0]
        self.dsdb_expect_delete(ip)
        # XXX The DNS record is retained, so the address should be added back
        # without the interface info
        # self.dsdb_expect_add("arecord13.aqd-unittest.ms.com", ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--ip", ip, "--keep_dns"]
        self.noouttest(command)
        self.dsdb_verify()

    def testrejectunknownip(self):
        ip = self.net.unknown[0].usable[10]
        command = ["del", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth1", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface eth1 of machine unittest00.one-nyp.ms.com "
                         "does not have IP address %s assigned to it." % ip,
                         command)

    def testrejectprimaryip(self):
        ip = self.net.unknown[0].usable[2]
        command = ["del", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth0", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The primary IP address of a hardware entity "
                         "cannot be removed.",
                         command)

    def testverifykeepdns(self):
        command = ["show", "fqdn",
                   "--fqdn", "unittest20-e1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest20-e1.aqd-unittest.ms.com", command)

    def testdelbylabel(self):
        ip = self.net.unknown[12].usable[3]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "1"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelbylabelagain(self):
        ip = self.net.unknown[12].usable[3]
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface eth1 of machine unittest20.aqd-unittest.ms.com "
                         "does not have an address with label 1.",
                         command)

    def testdelunittest20e0(self):
        ip = self.net.unknown[11].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelzebraeth0(self):
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--label", "zebra2"]
        self.noouttest(command)

    def testdelzebraeth1(self):
        ip = self.net.unknown[13].usable[1]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "zebra2"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyunittest20(self):
        ip = self.net.unknown[13].usable[0]
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"/system/network/vips" = nlist\(\s*'
                          r'"hostname", nlist\(\s*'
                          r'"interfaces", list\(\s*'
                          r'"eth0",\s*"eth1"\s*\),\s*'
                          r'"ip", "%s"\s*\)\s*'
                          r'\);' % ip,
                          command)
        self.matchclean(out, "aliases", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelInterfaceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
