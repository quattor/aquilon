#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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
"""Module for testing the add dynamic range command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from ipaddr import IPv4Address
from brokertest import TestBrokerCommand

def dynname(ip, domain="aqd-unittest.ms.com"):
    return "dynamic-%s.%s" % (str(ip).replace(".", "-"), domain)


class TestAddDynamicRange(TestBrokerCommand):

    def testadddifferentnetworks(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.net.tor_net2[0].usable[2],
                   "--endip=%s" % self.net.tor_net2[1].usable[2],
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "must be on the same subnet", command)

    def testaddmissingdomain(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.net.tor_net2[0].usable[2],
                   "--endip=%s" % self.net.tor_net2[0].usable[-3],
                   "--dns_domain=dns_domain_does_not_exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DNS Domain dns_domain_does_not_exist not found",
                         command)

    def testaddrange(self):
        messages = []
        for ip in range(int(self.net.tor_net2[0].usable[2]),
                        int(self.net.tor_net2[0].usable[-3]) + 1):
            address = IPv4Address(ip)
            hostname = dynname(address)
            self.dsdb_expect_add(hostname, address)
            messages.append("Adding %s [%s] to DSDB." % (hostname, address))

        command = ["add_dynamic_range",
                   "--startip=%s" % self.net.tor_net2[0].usable[2],
                   "--endip=%s" % self.net.tor_net2[0].usable[-3],
                   "--dns_domain=aqd-unittest.ms.com"]
        err = self.statustest(command)
        for message in messages:
            self.matchoutput(err, message, command)
        self.dsdb_verify()

    def testverifyrange(self):
        command = "search_dns --record_type=dynamic_stub"
        out = self.commandtest(command.split(" "))
        # Assume that first three octets are the same.
        start = self.net.tor_net2[0].usable[2]
        end = self.net.tor_net2[0].usable[-3]
        checked = False
        for i in range(int(start), int(end) + 1):
            checked = True
            ip = IPv4Address(i)
            self.matchoutput(out, dynname(ip), command)
            subcommand = ["search_dns", "--ip", ip, "--fqdn", dynname(ip)]
            subout = self.commandtest(subcommand)
            self.matchoutput(subout, dynname(ip), command)
        self.failUnless(checked, "Problem with test algorithm or data.")

    def testshowrange(self):
        net = self.net.tor_net2[0]
        start = net.usable[2]
        end = net.usable[-3]
        command = "show dynamic range --ip %s" % IPv4Address(int(start) + 1)
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Range: %s - %s" % (start, end), command)
        self.matchoutput(out, "Network: %s [%s]" % (net.ip, net),
                         command)

    def testverifynetwork(self):
        command = "show network --ip %s" % self.net.tor_net2[0].ip
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Ranges: %s-%s" %
                         (self.net.tor_net2[0].usable[2],
                          self.net.tor_net2[0].usable[-3]), command)

    def testverifynetworkproto(self):
        command = "show network --ip %s --format proto" % self.net.tor_net2[0].ip
        out = self.commandtest(command.split(" "))
        msg = self.parse_netlist_msg(out, expect=1)
        network = msg.networks[0]
        hosts = set([host.fqdn for host in network.hosts])
        start = self.net.tor_net2[0].usable[2]
        end = self.net.tor_net2[0].usable[-3]
        for i in range(int(start), int(end) + 1):
            ip = IPv4Address(i)
            self.failUnless(dynname(ip) in hosts, "%s is missing from network"
                            "protobuf output" % dynname(ip))

    def testfailalreadytaken(self):
        command = ["add_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[2],
                   "--endip", self.net.tor_net2[0].usable[3],
                   "--prefix=oops",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the following hosts already exist", command)
        self.matchoutput(out, "%s [%s]" %
                         (dynname(self.net.tor_net2[0].usable[2]),
                          self.net.tor_net2[0].usable[2]), command)
        self.matchoutput(out, "%s [%s]" %
                         (dynname(self.net.tor_net2[0].usable[3]),
                          self.net.tor_net2[0].usable[3]), command)

    def testaddendingrange(self):
        # Set up a network that has its final IP address taken.
        ip = self.net.tor_net2[1].usable[-1]
        hostname = dynname(ip)
        self.dsdb_expect_add(hostname, ip)
        command = ["add_dynamic_range", "--startip", ip, "--endip", ip,
                   "--dns_domain=aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Adding %s [%s] to DSDB." % (hostname, ip),
                         command)
        self.dsdb_verify()

    def testfailaddrestricted(self):
        command = ["add_dynamic_range",
                   "--startip", self.net.tor_net2[1].reserved[0],
                   "--endip", self.net.tor_net2[1].reserved[1],
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The IP address %s is reserved for dynamic "
                         "DHCP for a switch on subnet %s" %
                         (self.net.tor_net2[1].reserved[0],
                          self.net.tor_net2[1].ip),
                         command)

    def testdsdbrollback(self):
        for ip in range(int(self.net.tor_net2[2].usable[2]),
                        int(self.net.tor_net2[2].usable[4]) + 1):
            self.dsdb_expect_add(dynname(IPv4Address(ip)), IPv4Address(ip))
            self.dsdb_expect_delete(IPv4Address(ip))
        bad_ip = self.net.tor_net2[2].usable[5]
        self.dsdb_expect_add(dynname(bad_ip), bad_ip, fail=True)
        command = ["add_dynamic_range",
                   "--startip", self.net.tor_net2[2].usable[2],
                   "--endip", self.net.tor_net2[2].usable[5],
                   "--dns_domain", "aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.dsdb_verify()
        self.matchoutput(out, "Could not add addresses to DSDB", command)

    def testfillnetwork(self):
        messages = []
        for ip in range(int(self.net.tor_net2[5].usable[0]),
                        int(self.net.tor_net2[5].usable[-1]) + 1):
            address = IPv4Address(ip)
            hostname = dynname(address)
            self.dsdb_expect_add(hostname, address)
            messages.append("Adding %s [%s] to DSDB." % (hostname, address))
        command = ["add_dynamic_range",
                   "--fillnetwork", self.net.tor_net2[5].ip,
                   "--dns_domain=aqd-unittest.ms.com"]
        err = self.statustest(command)
        for message in messages:
            self.matchoutput(err, message, command)
        self.dsdb_verify()

    def testverifyfillnetwork(self):
        # Check that the network has only dynamic entries
        checkip = self.net.tor_net2[5].ip
        while checkip < self.net.tor_net2[5].usable[0]:
            command = ['search_dns', '--ip', checkip]
            self.noouttest(command)
            checkip += 1
        for ip in self.net.tor_net2[5].usable:
            command = ['search_dns', '--ip', checkip,
                       '--record_type=dynamic_stub']
            out = self.commandtest(command)
            self.matchoutput(out, 'aqd-unittest.ms.com', command)
        broadcast = self.net.tor_net2[5].broadcast
        command = ['search_dns', '--ip', broadcast]
        self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDynamicRange)
    unittest.TextTestRunner(verbosity=2).run(suite)
