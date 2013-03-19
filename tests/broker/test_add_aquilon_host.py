#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the add aquilon host command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddAquilonHost(TestBrokerCommand):

    def testaddunittest00(self):
        ip = self.net.unknown[0].usable[2]
        self.dsdb_expect_add("unittest00.one-nyp.ms.com", ip, "eth0", ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest00.one-nyp.ms.com", "--ip", ip,
                        "--machine", "ut3c1n3", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "inventory", "--buildstatus", "blind"])
        self.dsdb_verify()

    def testverifyaddunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest00.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[2],
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: inventory", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: blind", command)
        self.matchoutput(out, "Advertise Status: False", command)

    def testverifyshowmanagermissing(self):
        command = "show manager --missing"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            "aq add manager --hostname 'unittest00.one-nyp.ms.com' --ip 'IP'",
            command)

    def testverifyshowmanagermissingcsv(self):
        command = "show manager --missing --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testaddunittest12(self):
        ip = self.net.unknown[0].usable[7]
        self.dsdb_expect_add("unittest12.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest12.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "blind",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--machine", "ut3s01p1a", "--domain", "unittest"])
        self.dsdb_verify()

    def testverifyaddunittest12(self):
        command = "show host --hostname unittest12.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest12.aqd-unittest.ms.com [%s]" %
                         self.net.unknown[0].usable[7],
                         command)
        self.matchoutput(out, "Rackmount: ut3s01p1a", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: inventory", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: blind", command)

    def testaddunittest13(self):
        ip = self.net.unknown[0].usable[8]
        self.dsdb_expect_add("unittest13.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest13.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "blind",
                        "--machine", "ut3s01p1b", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyaddunittest13(self):
        command = "show host --hostname unittest13.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest13.aqd-unittest.ms.com [%s]" %
                         self.net.unknown[0].usable[8],
                         command)
        self.matchoutput(out, "Rackmount: ut3s01p1b", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: blind", command)

    def testaddunittest20bad(self):
        ip = self.net.unknown[13].usable[2]
        command = ["add", "aquilon", "host",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--ip", ip, "--buildstatus", "build",
                   "--zebra_interfaces", "eth0,eth2",
                   "--machine", "ut3c5n2", "--domain", "unittest",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine unittest20.aqd-unittest.ms.com does not "
                         "have an interface named eth2.", command)

    def testaddunittest20e1(self):
        # Add the transit before the host to verify that the reverse DNS entry
        # will get fixed up
        ip = self.net.unknown[12].usable[0]
        fqdn = "unittest20-e1.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add(fqdn, ip, "eth1", ip.mac)
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--fqdn", fqdn]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddunittest20good(self):
        ip = self.net.unknown[13].usable[2]
        eth1_ip = self.net.unknown[12].usable[0]
        self.dsdb_expect_add("unittest20.aqd-unittest.ms.com", ip, "le0")
        self.dsdb_expect_delete(eth1_ip)
        self.dsdb_expect_add("unittest20-e1.aqd-unittest.ms.com", eth1_ip, "eth1",
                             eth1_ip.mac, primary="unittest20.aqd-unittest.ms.com")
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--zebra_interfaces", "eth0,eth1",
                        "--machine", "ut3c5n2", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyunittest20(self):
        ip = self.net.unknown[13].usable[2]
        eth0_ip = self.net.unknown[11].usable[0]
        eth1_ip = self.net.unknown[12].usable[0]
        command = ["show", "host", "--hostname",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r"Interface: eth0 %s \[boot, default_route\]" %
                          eth0_ip.mac, command)
        self.searchoutput(out, r"Interface: eth1 %s \[default_route\]" %
                          eth1_ip.mac, command)
        self.matchoutput(out,
                         "Provides: unittest20.aqd-unittest.ms.com [%s] "
                         "(label: hostname, service_holder: host)" % ip,
                         command)
        self.matchoutput(out,
                         "Provides: unittest20-e1.aqd-unittest.ms.com [%s]" % eth1_ip,
                         command)

    def testverifyunittest20hostname(self):
        ip = self.net.unknown[13].usable[2]
        command = ["show", "service", "address", "--name", "hostname",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service Address: hostname", command)
        self.matchoutput(out, "Bound to: Host unittest20.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Address: unittest20.aqd-unittest.ms.com [%s]" % ip,
                         command)
        self.matchoutput(out, "Interfaces: eth0, eth1", command)

    def testverifyunittest20e1(self):
        command = ["show", "address",
                   "--fqdn", "unittest20-e1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: unittest20-e1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[12].usable[0],
                         command)
        self.matchoutput(out, "Reverse PTR: unittest20.aqd-unittest.ms.com",
                         command)

    def testaddunittest21(self):
        ip = self.net.unknown[11].usable[1]
        self.dsdb_expect_add("unittest21.aqd-unittest.ms.com", ip, "bond0")
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest21.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--machine", "ut3c5n3", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyunittest21network(self):
        net = self.net.unknown[11]
        ip = net.usable[1]
        command = ["show", "network", "--ip", net.ip, "--format", "proto"]
        out = self.commandtest(command)

        msg = self.parse_netlist_msg(out, expect=1)
        network = msg.networks[0]
        seen = False
        macs = [ip.mac]  # , self.net.unknown[12].usable[1].mac]
        for host in network.hosts:
            if host.ip != str(ip):
                continue

            seen = True
            self.failUnless(host.archetype.name == "aquilon",
                            "archetype is '%s' instead of aquilon" %
                            host.archetype.name)
            self.failUnless(host.mac in macs,
                            "MAC is '%s' instead of %r" %
                            (host.mac, macs))
            macs.remove(host.mac)

        self.failUnless(seen,
                        "%s is missing from network protobuf output" % ip)

    def testaddunittest22(self):
        ip = self.net.unknown[11].usable[2]
        self.dsdb_expect_add("unittest22.aqd-unittest.ms.com", ip, "br0")
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest22.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--machine", "ut3c5n4", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyunittest22network(self):
        net = self.net.unknown[11]
        ip = net.usable[2]
        command = ["show", "network", "--ip", net.ip, "--format", "proto"]
        out = self.commandtest(command)

        msg = self.parse_netlist_msg(out, expect=1)
        network = msg.networks[0]
        seen = False
        macs = [ip.mac]  # , self.net.unknown[12].usable[2].mac]
        for host in network.hosts:
            if host.ip != str(ip):
                continue

            seen = True
            self.failUnless(host.archetype.name == "aquilon",
                            "archetype is '%s' instead of aquilon" %
                            host.archetype.name)
            self.failUnless(host.mac in macs,
                            "MAC is '%s' instead of %r" %
                            (host.mac, macs))
            macs.remove(host.mac)

        self.failUnless(seen,
                        "%s is missing from network protobuf output" % ip)

    def testaddunittest23(self):
        ip = self.net.vpls[0].usable[1]
        self.dsdb_expect_add("unittest23.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest23.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--machine", "ut3c5n5", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testaddunittest24(self):
        ip = self.net.vpls[0].usable[2]
        self.dsdb_expect_add("unittest24.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest24.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--machine", "np3c5n5", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testaddunittest25(self):
        ip = self.net.unknown[0].usable[20]
        self.dsdb_expect_add("unittest25.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest25.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--machine", "ut3c5n7", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testaddunittest26(self):
        ip = self.net.unknown[0].usable[23]
        self.dsdb_expect_add("unittest26.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "aquilon", "host",
                        "--hostname", "unittest26.aqd-unittest.ms.com",
                        "--ip", ip, "--buildstatus", "build",
                        "--machine", "ut3c5n8", "--domain", "unittest",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAquilonHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
