#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
        for ip in range(int(self.net.tor_net2[0].usable[2]),
                        int(self.net.tor_net2[0].usable[-3]) + 1):
            self.dsdb_expect_add(dynname(IPv4Address(ip)), IPv4Address(ip))

        command = ["add_dynamic_range",
                   "--startip=%s" % self.net.tor_net2[0].usable[2],
                   "--endip=%s" % self.net.tor_net2[0].usable[-3],
                   "--dns_domain=aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyrange(self):
        command = "search_system --type=dynamic_stub"
        out = self.commandtest(command.split(" "))
        # Assume that first three octets are the same.
        start = self.net.tor_net2[0].usable[2]
        end = self.net.tor_net2[0].usable[-3]
        checked = False
        for i in range(int(start), int(end) + 1):
            checked = True
            ip = IPv4Address(i)
            self.matchoutput(out, dynname(ip), command)
            subcommand = ["search_system", "--ip", ip, "--fqdn", dynname(ip)]
            subout = self.commandtest(subcommand)
            self.matchoutput(subout, dynname(ip), command)
        self.failUnless(checked, "Problem with test algorithm or data.")

    def testverifynetwork(self):
        command = "show network --ip %s" % self.net.tor_net2[0].ip
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Ranges: %s-%s" %
                         (self.net.tor_net2[0].usable[2],
                          self.net.tor_net2[0].usable[-3]), command)

    def testfailalreadytaken(self):
        command = ["add_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[2],
                   "--endip", self.net.tor_net2[0].usable[3],
                   "--prefix=oops",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the following hosts already exist", command)
        self.matchoutput(out, "%s (%s)" %
                         (dynname(self.net.tor_net2[0].usable[2]),
                          self.net.tor_net2[0].usable[2]), command)
        self.matchoutput(out, "%s (%s)" %
                         (dynname(self.net.tor_net2[0].usable[3]),
                          self.net.tor_net2[0].usable[3]), command)

    def testaddendingrange(self):
        # Set up a network that has its final IP address taken.
        ip = self.net.tor_net2[1].usable[-1]
        self.dsdb_expect_add(dynname(ip), ip)
        command = ["add_dynamic_range", "--startip", ip, "--endip", ip,
                   "--dns_domain=aqd-unittest.ms.com"]
        self.noouttest(command)
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDynamicRange)
    unittest.TextTestRunner(verbosity=2).run(suite)
