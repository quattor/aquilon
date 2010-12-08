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
"""Module for testing the add interface address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

def dynname(ip, domain="aqd-unittest.ms.com"):
    return "dynamic-%s.%s" % (str(ip).replace(".", "-"), domain)


class TestAddInterfaceAddress(TestBrokerCommand):

    def testaddunittest20e0(self):
        ip = self.net.unknown[11].usable[0]
        fqdn = "unittest20-e0.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth0", ip.mac,
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--fqdn", fqdn, "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddunittest20e1(self):
        ip = self.net.unknown[12].usable[0]
        fqdn = "unittest20-e1.aqd-unittest.ms.com"
        # XXX The old DNS record should be deleted from DSDB
        # self.dsdb_expect_delete(ip)
        self.dsdb_expect_add(fqdn, ip, "eth1", ip.mac,
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--fqdn", fqdn]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddbyip(self):
        ip = self.net.unknown[12].usable[3]
        fqdn = "unittest20-e1-1.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth1:1",
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "1",
                   "--fqdn", fqdn, "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testrejectprimaryip(self):
        command = ["add", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "unittest01.one-nyp.ms.com",
                   "--ip", self.net.unknown[0].usable[10]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is used as a primary name", command)

    def testrejectduplicatelabel(self):
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "1",
                   "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already has an alias named", command)

    def testrejectduplicateuse(self):
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "2",
                   "--fqdn", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Non-zebra addresses cannot be assigned to "
                         "multiple machines/interfaces.", command)

    def testrejectdyndns(self):
        # Dynamic DHCP address, set up using add_dynamic_range
        ip = self.net.tor_net2[0].usable[2]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "3",
                   "--fqdn", "dyndhcp.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Address %s [%s] is reserved for dynamic DHCP." %
                         (dynname(ip), ip),
                         command)

    def testrejectreserved(self):
        # Address in the reserved range
        ip = self.net.tor_net2[0].reserved[0]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "3",
                   "--fqdn", "dyndhcp.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The IP address %s is reserved for dynamic DHCP for "
                         "a switch on subnet %s." %
                         (ip, self.net.tor_net2[0].ip),
                         command)

    def testsystemzebramix(self):
        ip = self.net.unknown[0].usable[3]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "2",
                   "--usage", "zebra",
                   "--fqdn", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already used by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com and is "
                         "not configured for Zebra." % ip,
                         command)

    def testaddzebraeth0(self):
        ip = self.net.unknown[13].usable[1]
        self.dsdb_expect_add("zebra.aqd-unittest.ms.com", ip, "vip",
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--label", "zebra2",
                   "--usage", "zebra",
                   "--fqdn", "zebra.aqd-unittest.ms.com", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddzebraeth1(self):
        ip = self.net.unknown[13].usable[1]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "zebra2",
                   "--usage", "zebra",
                   "--fqdn", "zebra.aqd-unittest.ms.com", "--ip", ip]
        self.noouttest(command)

    def test_failslaveaddress(self):
        # eth1 is enslaved to bond0
        command = ["add", "interface", "address", "--machine", "ut3c5n3",
                   "--interface", "eth1", "--fqdn",
                   "arecord14.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Slave interfaces cannot hold addresses.",
                         command)

    def testverifyunittest20(self):
        ip = self.net.unknown[13].usable[1]
        command = ["show", "host", "--hostname",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Provides: zebra.aqd-unittest.ms.com [%s] "
                         "(label: zebra2, usage: zebra)" % ip,
                         command)
        self.matchclean(out, "Auxiliary: zebra.aqd-unittest.ms.com", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterfaceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
