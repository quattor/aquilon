#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelAddress(TestBrokerCommand):

    def testbasic(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[13])
        command = ["del_address", "--ip=%s" % self.net.unknown[0].usable[13]]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifybasic(self):
        command = ["show_address", "--fqdn=arecord13.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def testdefaultenv(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[14])
        default = self.config.get("site", "default_dns_environment")
        command = ["del_address", "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", default]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifydefaultenv(self):
        command = ["show_address", "--fqdn=arecord14.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def testutenvenv(self):
        command = ["del_address", "--ip", self.net.unknown[1].usable[14],
                   "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        self.noouttest(command)

    def testverifyutenvenv(self):
        command = ["show_address", "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        self.notfoundtest(command)

    def testbadip(self):
        ip = self.net.unknown[0].usable[14]
        command = ["del_address", "--ip", ip,
                   "--fqdn=arecord15.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Record arecord15.aqd-unittest.ms.com, ip "
                         "%s not found." % ip, command)

    def testcleanup(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[15])
        command = ["del_address", "--ip=%s" % self.net.unknown[0].usable[15],
                   "--fqdn=arecord15.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testfailbadenv(self):
        default = self.config.get("site", "default_dns_environment")
        command = ["del_address", "--ip=%s" % self.net.unknown[0].usable[15],
                   "--fqdn=arecord15.aqd-unittest.ms.com",
                   "--dns_environment=environment-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DNS Environment environment-does-not-exist not found.",
                         command)

    def testfailprimary(self):
        ip = self.net.unknown[0].usable[2]
        command = ["del", "address", "--ip", ip, "--fqdn",
                   "unittest00.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record unittest00.one-nyp.ms.com [%s] is the "
                         "primary name of machine unittest00.one-nyp.ms.com, "
                         "therefore it cannot be deleted." % ip,
                         command)

    def testfailipinuse(self):
        ip = self.net.unknown[0].usable[3]
        command = ["del", "address", "--ip", ip, "--fqdn",
                   "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is still in use by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com" % ip,
                         command)

    def testdelunittest20_e1(self):
        ip = self.net.unknown[12].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "address", "--ip", ip,
                   "--fqdn", "unittest20-e1.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelzebra3(self):
        ip = self.net.unknown[13].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "address", "--ip", ip,
                   "--fqdn", "zebra3.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_delip_with_network_env(self):
        ip = "192.168.3.1"
        fqdn = "cardenvtest600.aqd-unittest.ms.com"
        command = ["del", "address", "--ip", ip,
                   "--network_environment", "cardenv"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

        command = ["show_address", "--fqdn", fqdn,
                   "--network_environment", "cardenv"]
        out = self.notfoundtest(command)

    def test_delreservedreverse(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[32])
        command = ["del", "address",
                   "--fqdn", "arecord17.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_verifydelreserve(self):
        command = ["show", "address",
                   "--fqdn", "arecord17.aqd-unittest.ms.com"]
        self.notfoundtest(command)

        command = ["search", "dns", "--record_type", "reserved_name"]
        out = self.commandtest(command)
        self.matchclean(out, "reverse.restrict.aqd-unittest.ms.com", command)
        self.matchclean(out, "reverse2.restrict.aqd-unittest.ms.com", command)

    def test_610_addipfromip_with_network_env(self):
        fqdn = "cardenvtest610.aqd-unittest.ms.com"
        command = ["del", "address", "--fqdn", fqdn,
                   "--network_environment", "cardenv"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

        command = ["show_address", "--fqdn=%s" % fqdn]
        out = self.notfoundtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
