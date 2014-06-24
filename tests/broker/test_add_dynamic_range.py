#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the add dynamic range command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from ipaddr import IPv4Address
from brokertest import TestBrokerCommand


class TestAddDynamicRange(TestBrokerCommand):
    def test_000_add_networks(self):
        self.net.allocate_network(self, "dyndhcp0", 25, "tor_net2",
                                  "building", "ut")
        self.net.allocate_network(self, "dyndhcp1", 25, "tor_net2",
                                  "building", "ut")
        self.net.allocate_network(self, "dyndhcp2", 28, "unknown",
                                  "building", "ut")
        self.net.allocate_network(self, "dyndhcp3", 28, "unknown",
                                  "building", "ut")
        self.net.allocate_network(self, "dyndhcp4", 28, "unknown",
                                  "building", "cards")

    def test_100_add_range(self):
        messages = []
        for ip in range(int(self.net["dyndhcp0"].usable[2]),
                        int(self.net["dyndhcp0"].usable[-3]) + 1):
            address = IPv4Address(ip)
            hostname = self.dynname(address)
            self.dsdb_expect_add(hostname, address)
            messages.append("DSDB: add_host -host_name %s -ip_address %s "
                            "-status aq" % (hostname, address))

        command = ["add_dynamic_range",
                   "--startip=%s" % self.net["dyndhcp0"].usable[2],
                   "--endip=%s" % self.net["dyndhcp0"].usable[-3],
                   "--dns_domain=aqd-unittest.ms.com"]
        err = self.statustest(command)
        for message in messages:
            self.matchoutput(err, message, command)
        self.dsdb_verify()

    def test_105_verify_range(self):
        command = "search_dns --record_type=dynamic_stub"
        out = self.commandtest(command.split(" "))
        # Assume that first three octets are the same.
        start = self.net["dyndhcp0"].usable[2]
        end = self.net["dyndhcp0"].usable[-3]
        checked = False
        for i in range(int(start), int(end) + 1):
            checked = True
            ip = IPv4Address(i)
            self.matchoutput(out, self.dynname(ip), command)
            subcommand = ["search_dns", "--ip", ip, "--fqdn", self.dynname(ip)]
            subout = self.commandtest(subcommand)
            self.matchoutput(subout, self.dynname(ip), command)
        self.failUnless(checked, "Problem with test algorithm or data.")

    def test_105_show_range(self):
        net = self.net["dyndhcp0"]
        start = net.usable[2]
        end = net.usable[-3]
        command = "show dynamic range --ip %s" % IPv4Address(int(start) + 1)
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Range: %s - %s" % (start, end), command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net),
                         command)

    def test_105_show_fqdn(self):
        net = self.net["dyndhcp0"]
        start = net.usable[2]
        end = net.usable[-3]
        command = ["show", "dynamic", "range", "--fqdn", self.dynname(end)]
        out = self.commandtest(command)
        self.matchoutput(out, "Dynamic Range: %s - %s" % (start, end), command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net),
                         command)

    def test_105_verify_network(self):
        command = "show network --ip %s" % self.net["dyndhcp0"].ip
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Ranges: %s-%s" %
                         (self.net["dyndhcp0"].usable[2],
                          self.net["dyndhcp0"].usable[-3]), command)

    def test_105_verify_network_proto(self):
        command = "show network --ip %s --format proto" % self.net["dyndhcp0"].ip
        out = self.commandtest(command.split(" "))
        msg = self.parse_netlist_msg(out, expect=1)
        network = msg.networks[0]
        hosts = set([host.fqdn for host in network.hosts])
        start = self.net["dyndhcp0"].usable[2]
        end = self.net["dyndhcp0"].usable[-3]
        for i in range(int(start), int(end) + 1):
            ip = IPv4Address(i)
            self.failUnless(self.dynname(ip) in hosts, "%s is missing from network"
                            "protobuf output" % self.dynname(ip))

    def test_110_add_end_in_grange(self):
        # Set up a network that has its final IP address taken.
        ip = self.net["dyndhcp1"].usable[-1]
        hostname = self.dynname(ip)
        self.dsdb_expect_add(hostname, ip)
        command = ["add_dynamic_range", "--startip", ip, "--endip", ip,
                   "--dns_domain=aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "DSDB: add_host -host_name %s -ip_address %s "
                         "-status aq" % (hostname, ip),
                         command)
        self.dsdb_verify()

    def test_120_fillnetwork_default_domain(self):
        messages = []
        for ip in range(int(self.net["dyndhcp3"].usable[0]),
                        int(self.net["dyndhcp3"].usable[-1]) + 1):
            address = IPv4Address(ip)
            hostname = self.dynname(address, domain="one-nyp.ms.com")
            self.dsdb_expect_add(hostname, address)
            messages.append("DSDB: add_host -host_name %s -ip_address %s "
                            "-status aq" % (hostname, address))
        command = ["add_dynamic_range",
                   "--fillnetwork", self.net["dyndhcp3"].ip]
        err = self.statustest(command)
        for message in messages:
            self.matchoutput(err, message, command)
        self.dsdb_verify()

    def test_125_verify_fillnetwork(self):
        # Check that the network has only dynamic entries
        checkip = self.net["dyndhcp3"].ip
        while checkip < self.net["dyndhcp3"].usable[0]:
            command = ['search_dns', '--ip', checkip]
            self.noouttest(command)
            checkip += 1
        for ip in self.net["dyndhcp3"].usable:
            command = ['search_dns', '--ip', ip,
                       '--record_type=dynamic_stub']
            out = self.commandtest(command)
            self.matchoutput(out, self.dynname(ip, domain="one-nyp.ms.com"),
                             command)
        broadcast = self.net["dyndhcp3"].broadcast
        command = ['search_dns', '--ip', broadcast]
        self.noouttest(command)

    def test_130_dsdb_rollback(self):
        for ip in range(int(self.net["dyndhcp2"].usable[2]),
                        int(self.net["dyndhcp2"].usable[4]) + 1):
            self.dsdb_expect_add(self.dynname(IPv4Address(ip)), IPv4Address(ip))
            self.dsdb_expect_delete(IPv4Address(ip))
        bad_ip = self.net["dyndhcp2"].usable[5]
        self.dsdb_expect_add(self.dynname(bad_ip), bad_ip, fail=True)
        command = ["add_dynamic_range",
                   "--startip", self.net["dyndhcp2"].usable[2],
                   "--endip", self.net["dyndhcp2"].usable[5],
                   "--dns_domain", "aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.dsdb_verify()
        self.matchoutput(out, "Could not add addresses to DSDB", command)

    def test_200_different_networks(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.net["dyndhcp0"].usable[2],
                   "--endip=%s" % self.net["dyndhcp1"].usable[2],
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "must be on the same subnet", command)

    def test_200_missing_domain(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.net["dyndhcp0"].usable[2],
                   "--endip=%s" % self.net["dyndhcp0"].usable[-3],
                   "--dns_domain=dns_domain_does_not_exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DNS Domain dns_domain_does_not_exist not found",
                         command)

    def test_200_ip_already_taken(self):
        command = ["add_dynamic_range",
                   "--startip", self.net["tor_net_12"].usable[0],
                   "--endip", self.net["tor_net_12"].usable[1],
                   "--prefix=oops",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the following IP addresses are already in use",
                         command)
        self.matchoutput(out, str(self.net["tor_net_12"].usable[0]), command)

    def test_200_dns_already_taken(self):
        command = ["add_dynamic_range",
                   "--startip", self.net["dyndhcp0"].usable[2],
                   "--endip", self.net["dyndhcp0"].usable[3],
                   "--prefix=oops",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the following DNS records already exist", command)
        self.matchoutput(out, "%s [%s]" %
                         (self.dynname(self.net["dyndhcp0"].usable[2]),
                          self.net["dyndhcp0"].usable[2]), command)
        self.matchoutput(out, "%s [%s]" %
                         (self.dynname(self.net["dyndhcp0"].usable[3]),
                          self.net["dyndhcp0"].usable[3]), command)

    def test_200_fail_add_restricted(self):
        command = ["add_dynamic_range",
                   "--startip", self.net["dyndhcp1"].reserved[0],
                   "--endip", self.net["dyndhcp1"].reserved[1],
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The IP address %s is reserved for dynamic "
                         "DHCP for a switch on subnet %s" %
                         (self.net["dyndhcp1"].reserved[0],
                          self.net["dyndhcp1"].ip),
                         command)

    def test_200_fail_no_default_dns_domain(self):
        command = ["add_dynamic_range", "--fillnetwork", self.net["dyndhcp4"].ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "There is no default DNS domain configured for "
                         "building cards.  Please specify --dns_domain.",
                         command)

    def test_800_cleanup(self):
        self.net.dispose_network(self, 'dyndhcp4')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDynamicRange)
    unittest.TextTestRunner(verbosity=2).run(suite)
