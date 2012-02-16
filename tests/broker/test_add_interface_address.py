#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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

    def testaddunittest20e0again(self):
        # No label, different IP
        ip = self.net.unknown[11].usable[-1]
        fqdn = "unittest20-e0.aqd-unittest.ms.com"
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--fqdn", fqdn, "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Public Interface eth0 of machine "
                         "unittest20.aqd-unittest.ms.com already "
                         "has an IP address.", command)

    def testaddunittest20e1(self):
        ip = self.net.unknown[12].usable[0]
        fqdn = "unittest20-e1.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add(fqdn, ip, "eth1", ip.mac,
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--fqdn", fqdn]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyunittest20network(self):
        # test_add_aquilon_host would be a better place for this test, but that
        # runs before test_add_interface_address so the transits are not set up
        # yet
        e0net = self.net.unknown[11]
        e0ip = e0net.usable[0]
        command = ["show", "network", "--ip", e0net.ip, "--format", "proto"]
        out = self.commandtest(command)

        msg = self.parse_netlist_msg(out, expect=1)
        network = msg.networks[0]
        ut20 = None
        for host in network.hosts:
            if host.ip == str(e0ip):
                ut20 = host
                break

        self.failUnless(ut20 is not None,
                        "%s is missing from network protobuf output" % e0ip)
        self.failUnless(ut20.archetype.name == "aquilon",
                        "archetype is '%s' instead of aquilon in protobuf output" %
                        ut20.archetype.name)
        self.failUnless(str(ut20.mac) == str(e0ip.mac),
                        "MAC is '%s' instead of %s in protobuf output" %
                        (ut20.mac, e0ip.mac))

    def testaddbyip(self):
        ip = self.net.unknown[12].usable[3]
        fqdn = "unittest20-e1-1.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth1_e1",
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e1",
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

    def testrejectnumericlabel(self):
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "1",
                   "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'1' is not a valid value for label", command)

    def testrejectduplicatelabel(self):
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e1",
                   "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already has an alias named", command)

    def testrejectduplicateuse(self):
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e2",
                   "--fqdn", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Non-zebra addresses cannot be assigned to "
                         "multiple machines/interfaces.", command)

    def testrejectdyndns(self):
        # Dynamic DHCP address, set up using add_dynamic_range
        ip = self.net.tor_net2[0].usable[2]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
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
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "dyndhcp.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The IP address %s is reserved for dynamic DHCP for "
                         "a switch on subnet %s." %
                         (ip, self.net.tor_net2[0].ip),
                         command)

    def testrejectbadusage(self):
        ip = self.net.tor_net2[0].usable[-1]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "badusage.aqd-unittest.ms.com", "--ip", ip,
                   "--usage", "badusage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal address usage 'badusage'.", command)

    def testrejectrestricteddomain(self):
        ip = self.net.tor_net2[0].usable[-1]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "foo.restrict.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, auxiliary addresses are not allowed.",
                         command)

    def testsystemzebramix(self):
        ip = self.net.unknown[0].usable[3]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e2",
                   "--usage", "zebra",
                   "--fqdn", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already used by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com and is "
                         "not configured for Zebra." % ip,
                         command)

    def testaddzebra2eth0(self):
        # Use an address that is smaller than the primary IP to verify that the
        # primary IP is not removed
        ip = self.net.unknown[13].usable[1]
        self.dsdb_expect_add("zebra2.aqd-unittest.ms.com", ip, "le1",
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--label", "zebra2",
                   "--usage", "zebra",
                   "--fqdn", "zebra2.aqd-unittest.ms.com", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddzebra2eth1(self):
        ip = self.net.unknown[13].usable[1]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "zebra2",
                   "--usage", "zebra",
                   "--fqdn", "zebra2.aqd-unittest.ms.com", "--ip", ip]
        self.noouttest(command)

    def testaddzebra3eth0(self):
        # Adding an even lower IP should cause zebra2 to be renumbered in DSDB
        zebra2_ip = self.net.unknown[13].usable[1]
        zebra3_ip = self.net.unknown[13].usable[0]
        self.dsdb_expect_delete(zebra2_ip)
        self.dsdb_expect_add("zebra3.aqd-unittest.ms.com", zebra3_ip, "le1",
                             primary="unittest20.aqd-unittest.ms.com")
        self.dsdb_expect_add("zebra2.aqd-unittest.ms.com", zebra2_ip, "le2",
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--label", "zebra3",
                   "--usage", "zebra",
                   "--fqdn", "zebra3.aqd-unittest.ms.com", "--ip", zebra3_ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddzebra3eth1(self):
        ip = self.net.unknown[13].usable[0]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "zebra3",
                   "--usage", "zebra",
                   "--fqdn", "zebra3.aqd-unittest.ms.com", "--ip", ip]
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
        zebra2_ip = self.net.unknown[13].usable[1]
        zebra3_ip = self.net.unknown[13].usable[0]
        command = ["show", "host", "--hostname",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Provides: zebra2.aqd-unittest.ms.com [%s] "
                         "(label: zebra2, usage: zebra)" % zebra2_ip,
                         command)
        self.matchoutput(out,
                         "Provides: zebra3.aqd-unittest.ms.com [%s] "
                         "(label: zebra3, usage: zebra)" % zebra3_ip,
                         command)
        self.matchclean(out, "Auxiliary: zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "Auxiliary: zebra3.aqd-unittest.ms.com", command)

    def testmixenvironments(self):
        net = self.net.unknown[1]
        ip = net[3]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth0", "--ip", ip, "--label", "e0",
                   "--fqdn", "unittest25-e0.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "utcolo"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Public Interface eth0 of machine "
                         "unittest25.aqd-unittest.ms.com already has an IP "
                         "address from network environment internal.  Network "
                         "environments cannot be mixed.",
                         command)

    def testbadmachine(self):
        command = ["add", "interface", "address", "--machine", "no-such-machine",
                   "--interface", "eth0", "--ip", "192.168.0.1",
                   "--fqdn", "foo.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Machine no-such-machine not found.", command)

    def testmissingnetenv(self):
        net = self.net.unknown[1]
        ip = net[3]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth0", "--ip", ip, "--label", "e0",
                   "--fqdn", "unittest25-e0.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "no-such-env"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Network Environment no-such-env not found.",
                         command)

    def testaddunittest25utcolo(self):
        net = self.net.unknown[1]
        ip = net[4]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth1", "--ip", ip,
                   "--fqdn", "unittest25-e1.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "utcolo"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

    def testaddunittest25excx(self):
        net_internal = self.net.unknown[0]
        net_excx = self.net.unknown[0].subnet()[0]
        ip = net_excx[3]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth2", "--ip", ip,
                   "--fqdn", "unittest25-e2.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "excx"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network %s in network environment internal used on "
                         "public interface eth0 of machine "
                         "unittest25.aqd-unittest.ms.com overlaps requested "
                         "network excx-net in network environment excx." % net_internal.ip,
                         command)

    def testverifyunittest23(self):
        command = ["show", "host", "--hostname", "unittest25.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        # Rely on the indentation to ensure we're checking the network
        # environment of the right interface
        self.searchoutput(out,
                          'Interface: eth0 .*\n'
                          '(?:    .*\n)*'
                          '    Network Environment: internal',
                          command)
        self.searchoutput(out,
                          'Interface: eth1 .*\n'
                          '(?:    .*\n)*'
                          '    Network Environment: utcolo',
                          command)

    def testaddunittest26(self):
        ip = self.net.unknown[14].usable[0]
        fqdn = "unittest26-e1.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth1", ip.mac,
                             primary="unittest26.aqd-unittest.ms.com")
        command = ["add", "interface", "address",
                   "--machine", "unittest26.aqd-unittest.ms.com",
                   "--interface", "eth1", "--ip", ip, "--fqdn", fqdn]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddut3gd1r04vlan110(self):
        ip = self.net.tor_net[12].usable[1]
        self.dsdb_expect_add("ut3gd1r04-vlan110.aqd-unittest.ms.com", ip,
                             "vlan110", primary="ut3gd1r04.aqd-unittest.ms.com")
        command = ["add", "interface", "address",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "vlan110", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyut3gd1r04(self):
        command = ["show", "switch", "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"Interface: vlan110 \(no MAC addr\)$"
                          r"\s+Type: oa$"
                          r"\s+Network Environment: internal$"
                          r"\s+Provides: ut3gd1r04-vlan110.aqd-unittest.ms.com \[%s\]$"
                          % self.net.tor_net[12].usable[1],
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterfaceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
