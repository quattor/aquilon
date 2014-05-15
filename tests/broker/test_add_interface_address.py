#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the add interface address command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from test_add_dynamic_range import dynname


class TestAddInterfaceAddress(TestBrokerCommand):

    def testaddunittest20e0(self):
        ip = self.net["zebra_eth0"].usable[0]
        fqdn = "unittest20-e0.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth0", ip.mac,
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--fqdn", fqdn, "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddunittest20e0again(self):
        ip = self.net["zebra_eth0"].usable[0]
        fqdn = "unittest20-e0.aqd-unittest.ms.com"
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--fqdn", fqdn, "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by public interface "
                         "eth0 of machine unittest20.aqd-unittest.ms.com." % ip,
                         command)

    def testaddunittest20e0namemismatch(self):
        # No label, different FQDN, different IP
        ip = self.net["zebra_eth0"].usable[-1]
        fqdn = "unittest20-e0-1.aqd-unittest.ms.com"
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--fqdn", fqdn, "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Public Interface eth0 of machine "
                         "unittest20.aqd-unittest.ms.com already "
                         "has an IP address.", command)

    def testaddunittest20e0ipmismatch(self):
        # No label, same FQDN, different IP
        ip = self.net["zebra_eth0"].usable[-1]
        fqdn = "unittest20-e0.aqd-unittest.ms.com"
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--fqdn", fqdn, "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Record unittest20-e0.aqd-unittest.ms.com "
                         "points to a different IP address.", command)

    def testverifyunittest20e0(self):
        command = ["show", "address",
                   "--fqdn", "unittest20-e0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: unittest20-e0.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net["zebra_eth0"].usable[0],
                         command)
        self.matchoutput(out, "Reverse PTR: unittest20.aqd-unittest.ms.com",
                         command)

    def testverifyunittest20network(self):
        # test_add_aquilon_host would be a better place for this test, but that
        # runs before test_add_interface_address so the transits are not set up
        # yet
        e0net = self.net["zebra_eth0"]
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
        ip = self.net["zebra_eth1"].usable[3]
        fqdn = "unittest20-e1-1.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth1_e1",
                             primary="unittest20.aqd-unittest.ms.com")
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e1",
                   "--fqdn", fqdn, "--ip", ip, "--nomap_to_primary"]
        self.noouttest(command)
        self.dsdb_verify()

    def testrejectprimaryip(self):
        command = ["add", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "unittest01.one-nyp.ms.com",
                   "--ip", self.net["unknown0"].usable[10]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record unittest01.one-nyp.ms.com is already used "
                         "as the primary name of machine ut3c1n4.",
                         command)

    def testrejecthostnamelabel(self):
        command = ["add", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth1", "--label", "hostname",
                   "--fqdn", "hostname-label.one-nyp.ms.com",
                   "--ip", self.net["unknown0"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The 'hostname' label can only be managed by "
                         "add_host/del_host.",
                         command)

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
        ip = self.net["unknown0"].usable[3]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e2",
                   "--fqdn", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com." % ip,
                         command)

    def testrejectdyndns(self):
        # The FQDN does not exist yet, but the IP is used for dynamic DHCP
        ip = self.net["dyndhcp0"].usable[2]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "dyndhcp.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Address %s [%s] is reserved for dynamic DHCP." %
                         (dynname(ip), ip), command)

    def testrejectdyndnsfqdn(self):
        # The FQDN exists and is used for dynamic DHCP
        ip = self.net["dyndhcp0"].usable[2]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", dynname(ip)]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Address %s [%s] is reserved for dynamic DHCP." %
                         (dynname(ip), ip), command)

    def testrejectreserved(self):
        # Address in the reserved range
        ip = self.net["dyndhcp0"].reserved[0]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "dyndhcp.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The IP address %s is reserved for dynamic DHCP for "
                         "a switch on subnet %s." %
                         (ip, self.net["dyndhcp0"].ip),
                         command)

    def testrejectrestricteddomain(self):
        ip = self.net["dyndhcp0"].usable[-1]
        command = ["add", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e3",
                   "--fqdn", "foo.restrict.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, adding extra addresses is not allowed.",
                         command)

    def test_failslaveaddress(self):
        # eth1 is enslaved to bond0
        command = ["add", "interface", "address", "--machine", "ut3c5n3",
                   "--interface", "eth1", "--fqdn",
                   "arecord14.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Slave interfaces cannot hold addresses.",
                         command)

    def testmixenvironments(self):
        net = self.net["unknown1"]
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
        net = self.net["unknown1"]
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
        net = self.net["unknown1"]
        ip = net[4]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth1", "--ip", ip,
                   "--fqdn", "unittest25-e1.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "utcolo"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

    def testverifyunittest25utcolo(self):
        command = ["show", "address", "--dns_environment", "ut-env",
                   "--fqdn", "unittest25-e1.utcolo.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Network Environment: utcolo", command)
        self.matchclean(out, "Reverse", command)

    def testaddunittest25utcolo2(self):
        net = self.net["unknown1"]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth2", "--ipfromip", net.ip,
                   "--fqdn", "unittest25-e2.utcolo.aqd-unittest.ms.com",
                   "--network_environment", "utcolo"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

    def testaddunittest25utcolo3(self):
        net = self.net["unknown1"]
        command = ["add", "interface", "address", "--machine", "ut3c5n7",
                   "--interface", "eth2", "--ipfromip", net.ip,
                   "--fqdn", "unittest25-e2-2.utcolo.aqd-unittest.ms.com",
                   "--label", "e2", "--map_to_primary",
                   "--network_environment", "utcolo"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine unittest25.aqd-unittest.ms.com lives in DNS "
                         "environment internal, not DNS environment ut-env.",
                         command)

    def testaddunittest25excx(self):
        net_internal = self.net["unknown0"]
        net_excx = self.net["unknown0"].subnet()[0]
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
                         "network excx-net in network environment excx." %
                         net_internal.name,
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
        self.searchoutput(out,
                          'Interface: eth2 .*\n'
                          '(?:    .*\n)*'
                          '    Network Environment: utcolo',
                          command)

    def testaddunittest26(self):
        ip = self.net["routing1"].usable[0]
        fqdn = "unittest26-e1.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip, "eth1", ip.mac,
                             primary="unittest26.aqd-unittest.ms.com")
        command = ["add", "interface", "address",
                   "--machine", "unittest26.aqd-unittest.ms.com",
                   "--interface", "eth1", "--ip", ip, "--fqdn", fqdn]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddut3gd1r04vlan110(self):
        ip = self.net["tor_net_12"].usable[1]
        self.dsdb_expect_add("ut3gd1r04-vlan110.aqd-unittest.ms.com", ip,
                             "vlan110", primary="ut3gd1r04.aqd-unittest.ms.com",
                             comments="Some new switch comments")
        command = ["add", "interface", "address",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "vlan110", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()
        self.check_plenary_contents('hostdata', 'ut3gd1r04.aqd-unittest.ms.com',
                                    contains=str(ip))

    def testaddut3gd1r04vlan110hsrp(self):
        ip = self.net["tor_net_12"].usable[2]
        self.dsdb_expect_add("ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com", ip,
                             "vlan110_hsrp", primary="ut3gd1r04.aqd-unittest.ms.com",
                             comments="Some new switch comments")
        command = ["add", "interface", "address",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "vlan110", "--label", "hsrp", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()
        self.check_plenary_contents('hostdata', 'ut3gd1r04.aqd-unittest.ms.com',
                                    contains=str(ip))

    def testaddut3gd1r04loop0(self):
        # Use the network address
        ip = self.net["autopg1"][0]
        self.dsdb_expect_add("ut3gd1r04-loop0.aqd-unittest.ms.com", ip,
                             "loop0", primary="ut3gd1r04.aqd-unittest.ms.com",
                             comments="Some new switch comments")
        command = ["add", "interface", "address",
                   "--network_device", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "loop0", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()
        self.check_plenary_contents('hostdata', 'ut3gd1r04.aqd-unittest.ms.com',
                                    contains=str(ip))

    def testverifyut3gd1r04(self):
        command = ["show", "network_device", "--network_device", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"Interface: vlan110 \(no MAC addr\)$"
                          r"\s+Type: virtual$"
                          r"\s+Network Environment: internal$"
                          r"\s+Provides: ut3gd1r04-vlan110.aqd-unittest.ms.com \[%s\]$"
                          r"\s+Provides: ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com \[%s\] \(label: hsrp\)$"
                          % (self.net["tor_net_12"].usable[1],
                             self.net["tor_net_12"].usable[2]),
                          command)
        self.searchoutput(out,
                          r"Interface: loop0 \(no MAC addr\)$"
                          r"\s+Type: loopback$"
                          r"\s+Network Environment: internal$"
                          r"\s+Provides: ut3gd1r04-loop0.aqd-unittest.ms.com \[%s\]$"
                          % self.net["autopg1"][0],
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInterfaceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
