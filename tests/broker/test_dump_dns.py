#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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
                         "Calias2alias.aqd-unittest.ms.com:alias2host.aqd-unittest.ms.com",
                         command)
        # SRV
        self.matchoutput(out,
                         r":_kerberos._tcp.aqd-unittest.ms.com:33:\000\012\000\024\000\130\011arecord14\014aqd-unittest\002ms\003com\000",
                         command)
        self.matchoutput(out,
                         r":_kerberos._tcp.aqd-unittest.ms.com:33:\000\012\000\024\000\130\011arecord15\014aqd-unittest\002ms\003com\000",
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
                         'alias2alias.aqd-unittest.ms.com.\tIN\tCNAME\talias2host.aqd-unittest.ms.com.',
                         command)
        # SRV
        self.matchoutput(out,
                         "_kerberos._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 88 arecord14.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(out,
                         "_kerberos._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 88 arecord15.aqd-unittest.ms.com.",
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
