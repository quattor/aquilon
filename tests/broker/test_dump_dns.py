#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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
"""Module for testing the dump_dns command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


def inaddr_ptr(ip):
    octets = str(ip).split('.')
    octets.reverse()
    return "%s.in-addr.arpa" % '.'.join(octets)


class TestDumpDns(TestBrokerCommand):

    def test_djb(self):
        command = ["dump", "dns"]
        out = self.commandtest(command, auth=False)
        # Primary name
        self.matchoutput(out,
                         "=unittest20.aqd-unittest.ms.com:%s" %
                         self.net["zebra_vip"].usable[2],
                         command)
        # Auxiliary address
        self.matchoutput(out,
                         "+unittest20-e0.aqd-unittest.ms.com:%s" %
                         self.net["zebra_eth0"].usable[0],
                         command)
        self.matchoutput(out,
                         "^%s:unittest20.aqd-unittest.ms.com" %
                         inaddr_ptr(self.net["zebra_eth0"].usable[0]),
                         command)
        # CNAME
        self.matchoutput(out,
                         "Calias2host.aqd-unittest.ms.com:arecord13.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out,
                         "Calias2alias.aqd-unittest.ms.com:alias2host.aqd-unittest.ms.com:60",
                         command)
        self.matchclean(out,
                        "Calias2host.aqd-unittest.ms.com:arecord13.aqd-unittest.ms.com:",
                        command)
        # SRV
        self.matchoutput(out,
                         r":_kerberos._tcp.aqd-unittest.ms.com:33:\000\012\000\024\000\130\011arecord14\014aqd-unittest\002ms\003com\000",
                         command)
        self.matchoutput(out,
                         r":_kerberos._tcp.aqd-unittest.ms.com:33:\000\012\000\024\000\130\011arecord15\014aqd-unittest\002ms\003com\000:3600",
                         command)
        self.matchoutput(out,
                         r":_ldap-restrict._tcp.aqd-unittest.ms.com:33:\000\012\000\024\001\205\004ldap\010restrict\014aqd-unittest\002ms\003com\000",
                         command)
        self.matchoutput(out,
                         r":_ldap-alias._tcp.aqd-unittest.ms.com:33:\000\012\000\024\001\205\012alias2host\014aqd-unittest\002ms\003com\000",
                         command)
        self.matchoutput(out,
                         r":_ldap-reserved._udp.aqd-unittest.ms.com:33:\000\012\000\024\001\205\006nyaqd1\002ms\003com\000",
                         command)
        self.matchoutput(out,
                         r":_http._tcp.aqd-unittest.ms.com:33:\000\062\000\012\037\220\012addralias1\014aqd-unittest\002ms\003com\000",
                         command)
        # Address record
        self.matchoutput(out,
                         "=arecord40.aqd-unittest.ms.com:%s:300" %
                         self.net["unknown0"].usable[40],
                         command)
        self.matchclean(out,
                        "=arecord13.aqd-unittest.ms.com:%s:" %
                        self.net["unknown0"].usable[13],
                        command)
        # Address alias
        self.matchoutput(out,
                         "addralias1.aqd-unittest.ms.com:%s:1800" %
                         self.net["unknown0"].usable[14],
                         command)
        self.matchclean(out,
                        "addralias1.aqd-unittest.ms.com:%s:" %
                        self.net["unknown0"].usable[13],
                        command)
        self.matchclean(out,
                        "addralias1.aqd-unittest.ms.com:%s:" %
                        self.net["unknown0"].usable[15],
                        command)
        self.matchclean(out, "utcolo", command)

    def test_djb_domain(self):
        command = ["dump", "dns", "--dns_domain", "one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "aqd-unittest.ms.com", command)

    def test_djb_env(self):
        command = ["dump", "dns", "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        # The primary name is in a different DNS environment, so we can't
        # reference it in the reverse record
        self.matchoutput(out,
                         "=unittest25-e1.utcolo.aqd-unittest.ms.com:%s" %
                         self.net["unknown1"][4],
                         command)
        # Alias across differnet environment should be included
        self.matchoutput(out, "Calias2host.aqd-unittest-ut-env.ms.com:arecord13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Calias13.aqd-unittest.ms.com:arecord13.aqd-unittest.ms.com", command)
        # The target definition in different environment should not be included
        self.matchclean(out, "=arecord13.aqd-unittest.ms.com", command)

    def test_bind(self):
        command = ["dump", "dns", "--format", "raw"]
        out = self.commandtest(command)
        # Primary name
        self.matchoutput(out,
                         "unittest20.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net["zebra_vip"].usable[2],
                         command)
        self.matchoutput(out,
                         "%s.\tIN\tPTR\tunittest20.aqd-unittest.ms.com." %
                         inaddr_ptr(self.net["zebra_vip"].usable[2]),
                         command)
        # Auxiliary address
        self.matchoutput(out,
                         "unittest20-e0.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net["zebra_eth0"].usable[0],
                         command)
        self.matchoutput(out,
                         "%s.\tIN\tPTR\tunittest20.aqd-unittest.ms.com." %
                         inaddr_ptr(self.net["zebra_eth0"].usable[0]),
                         command)
        # CNAME
        self.matchoutput(out,
                         'alias2host.aqd-unittest.ms.com.\tIN\tCNAME\tarecord13.aqd-unittest.ms.com.',
                         command)
        self.matchoutput(out,
                         'alias2alias.aqd-unittest.ms.com.\t60\tIN\tCNAME\talias2host.aqd-unittest.ms.com.',
                         command)
        # SRV
        self.matchoutput(out,
                         "_kerberos._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 88 arecord14.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(out,
                         "_kerberos._tcp.aqd-unittest.ms.com.\t3600\tIN\tSRV\t"
                         "10 20 88 arecord15.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(out,
                         "_ldap-restrict._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 389 ldap.restrict.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(out,
                         "_ldap-alias._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 389 alias2host.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(out,
                         "_ldap-reserved._udp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 389 nyaqd1.ms.com.",
                         command)
        self.matchoutput(out,
                         "_http._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "50 10 8080 addralias1.aqd-unittest.ms.com.",
                         command)
        # Address record
        self.matchoutput(out,
                         "arecord40.aqd-unittest.ms.com.\t300\tIN\tA\t%s" %
                         self.net["unknown0"].usable[40],
                         command)
        self.matchoutput(out,
                         "%s.\t300\tIN\tPTR\tarecord40.aqd-unittest.ms.com." %
                         inaddr_ptr(self.net["unknown0"].usable[40]),
                         command)
        self.matchoutput(out,
                         "arecord13.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net["unknown0"].usable[13],
                         command)
        self.matchoutput(out,
                         "%s.\tIN\tPTR\tarecord13.aqd-unittest.ms.com." %
                         inaddr_ptr(self.net["unknown0"].usable[13]),
                         command)
        # Address alias
        self.matchoutput(out,
                         "addralias1.aqd-unittest.ms.com.\t1800\tIN\tA\t%s" %
                         self.net["unknown0"].usable[14],
                         command)
        self.matchoutput(out,
                         "addralias1.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net["unknown0"].usable[13],
                         command)
        self.matchoutput(out,
                         "addralias1.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net["unknown0"].usable[15],
                         command)
        self.matchclean(out, "utcolo", command)

    def test_bind_domain(self):
        command = ["dump", "dns", "--dns_domain", "one-nyp.ms.com",
                   "--format", "raw"]
        out = self.commandtest(command)
        self.matchclean(out, "aqd-unittest.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDumpDns)
    unittest.TextTestRunner(verbosity=2).run(suite)
