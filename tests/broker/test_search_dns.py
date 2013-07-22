#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the search dns command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchDns(TestBrokerCommand):
    def testbyip(self):
        net = self.net["unknown0"]
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
        self.matchoutput(out, "IP: %s" % self.net["unknown12"].usable[0],
                         command)
        self.matchoutput(out, "Assigned To: ut3c5n2/eth1", command)
        self.matchclean(out, "Primary Name", command)

    def testbydomain(self):
        command = ["search", "dns", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra2.aqd-unittest.ms.com", command)
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

    def testbytargetdomain(self):
        command = ["search", "dns", "--target_domain", "aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Alias: alias.ms.com", command)
        self.matchoutput(out, "Alias: alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Alias: alias2alias.aqd-unittest.ms.com", command)
        self.matchoutput(out, "SRV Record: _kerberos._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "SRV Record: _kerberos._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "SRV Record: _ldap._tcp.aqd-unittest.ms.com",
                         command)

    def testbynetwork(self):
        command = ["search", "dns", "--network", self.net["unknown0"].ip]
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
        command = ["search", "dns", "--network", self.net["unknown1"].ip,
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
                         self.net["unknown0"].usable[13], command)
        self.matchoutput(out,
                         "alias2host.aqd-unittest.ms.com,internal,CNAME,"
                         "arecord13.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "utcolo", command)

    def testused(self):
        command = ["search", "dns", "--used"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest20-e1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut9c1.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchclean(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchclean(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchclean(out, "_kerberos._tcp.aqd-unittest.ms.com", command)

    def testunused(self):
        command = ["search", "dns", "--unused"]
        out = self.commandtest(command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00r.one-nyp.ms.com", command)
        self.matchclean(out, "unittest20-e1.aqd-unittest.ms.com", command)
        self.matchclean(out, "zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "zebra3.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "_kerberos._tcp.aqd-unittest.ms.com", command)

    def testprimary(self):
        command = ["search", "dns", "--primary_name"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20-e0.aqd-unittest.ms.com", command)
        self.matchclean(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchclean(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchclean(out, "_kerberos._tcp.aqd-unittest.ms.com", command)

    def testnoprimary(self):
        command = ["search", "dns", "--noprimary_name"]
        out = self.commandtest(command)
        self.matchclean(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut9c1.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchclean(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest20-e0.aqd-unittest.ms.com", command)
        self.matchoutput(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "_kerberos._tcp.aqd-unittest.ms.com", command)

    def testbadtype(self):
        command = ["search", "dns", "--record_type", "no-such-rr"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown DNS record type 'no-such-rr'.", command)

    def testunittest20(self):
        command = ["search", "dns", "--reverse_ptr",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest20-e0.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest20-e1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra3.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20-e1-1.aqd-unittest.ms.com", command)
        self.matchclean(out, "zebra2.aqd-unittest.ms.com", command)

    def testptroverride(self):
        command = ["search", "dns", "--reverse_override"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest20-e0.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest20-e1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest26-e1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh51-e1.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20-e1-1.aqd-unittest.ms.com", command)
        self.matchclean(out, "zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "dynamic-", command)
        self.matchclean(out, "alias", command)
        self.matchclean(out, "_tcp.aqd-unittest.ms.com", command)

    def testptrnooverride(self):
        command = ["search", "dns", "--noreverse_override"]
        out = self.commandtest(command)
        self.matchclean(out, "unittest20-e0.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest20-e1.aqd-unittest.ms.com", command)
        self.matchclean(out, "zebra3.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest26-e1.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest20-e1-1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "zebra2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchoutput(out, "_kerberos._tcp.aqd-unittest.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchDns)
    unittest.TextTestRunner(verbosity=2).run(suite)
