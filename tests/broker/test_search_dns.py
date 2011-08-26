#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Module for testing the search dns command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchDns(TestBrokerCommand):
    def testbyip(self):
        net = self.net.unknown[0]
        ip = net.usable[2]
        command = ["search", "dns", "--ip", ip, "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out, "IP: %s" % ip, command)
        self.matchoutput(out, "Network: %s [%s]" % (net.ip, net), command)
        self.matchoutput(out, "Primary Name Of: Machine ut3c1n3", command)
        self.matchoutput(out, "Assigned To: ut3c1n3/eth0", command)

    def testbyfqdn(self):
        command = ["search", "dns", "--fqdn", "zebra2.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchclean(out, "Primary Name", command)
        self.matchoutput(out, "Assigned To: ut3c5n2/eth0, ut3c5n2/eth1", command)

    def testauxiliary(self):
        command = ["search", "dns", "--fqdn",
                   "unittest20-e1.aqd-unittest.ms.com", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[12].usable[0],
                         command)
        self.matchoutput(out, "Assigned To: ut3c5n2/eth1", command)
        self.matchclean(out, "Primary Name", command)

    def testbydomain(self):
        command = ["search", "dns", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np997gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np998gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np998gd1r02.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np999gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c5.aqd-unittest.ms.com", command)
        self.matchclean(out, "one-nyp.ms.com", command)

    def testbyshort(self):
        command = ["search", "dns", "--shortname", "unittest00"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testbytype(self):
        command = ["search", "dns", "--record_type", "reserved_name",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Reserved Name: %s" % self.aurora_with_node,
                         command)
        self.matchclean(out, "DNS Record:", command)
        self.matchclean(out, "Alias:", command)

    def testbytarget(self):
        command = ["search", "dns", "--target", "arecord13.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Alias: alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Aliases: alias2alias.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Target: arecord13.aqd-unittest.ms.com", command)

    def testbynetwork(self):
        command = ["search", "dns", "--network", self.net.unknown[0].ip]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchclean(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20-e0.aqd-unittest.ms.com", command)
        self.matchclean(out, "utcolo", command)

    def testbynetenv(self):
        command = ["search", "dns", "--network", self.net.unknown[1].ip,
                   "--network_environment", "utcolo"]
        out = self.commandtest(command)
        self.matchoutput(out, "gw1.utcolo.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest25-e1.utcolo.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "arecord13", command)
        # arecord14: dns_env=ut-env, net_env=internal
        self.matchclean(out, "arecord14", command)
        self.matchclean(out, "unittest00", command)
        self.matchclean(out, "alias", command)

    def testbydnsenv(self):
        command = ["search", "dns", "--record_type", "a",
                   "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        # arecord14: dns_env=ut-env, net_env=internal
        self.matchoutput(out, "arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "gw1.utcolo.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest25-e1.utcolo.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "unittest00", command)
        self.matchclean(out, "arecord13", command)

    def testcsv(self):
        command = ["search", "dns", "--dns_domain", "aqd-unittest.ms.com",
                   "--format", "csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord13.aqd-unittest.ms.com,internal,A,%s" %
                         self.net.unknown[0].usable[13], command)
        self.matchoutput(out,
                         "alias2host.aqd-unittest.ms.com,internal,CNAME,"
                         "arecord13.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "utcolo", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchDns)
    unittest.TextTestRunner(verbosity=2).run(suite)
