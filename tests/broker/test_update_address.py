#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
"""Module for testing the update address command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand


class TestUpdateAddress(TestBrokerCommand):

    def test_100_update_reverse(self):
        self.dsdb_expect_update("arecord15.aqd-unittest.ms.com",
                                comments="Test comment")
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord14.aqd-unittest.ms.com",
                   "--comments", "Test comment"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_verify_arecord15(self):
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Comments: Test comment", command)
        self.matchoutput(out, "Reverse PTR: arecord14.aqd-unittest.ms.com",
                         command)

    def test_105_search_ptr(self):
        command = ["search", "dns",
                   "--reverse_ptr", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord15.aqd-unittest.ms.com", command)

    def test_105_search_override(self):
        command = ["search", "dns", "--reverse_override"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord15.aqd-unittest.ms.com", command)

    def test_110_clear_ptr_override(self):
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord15.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)

    def test_115_verify_arecord15(self):
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def test_115_verify_search(self):
        command = ["search", "dns", "--reverse_override"]
        out = self.commandtest(command)
        self.matchclean(out, "arecord15.aqd-unittest.ms.com", command)

    def test_120_update_ip(self):
        old_ip = self.net["unknown0"].usable[15]
        ip = self.net["unknown0"].usable[-1]
        self.dsdb_expect_update("arecord15.aqd-unittest.ms.com", ip=ip)
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def test_125_verify_arecord15(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "IP: %s" % ip, command)

    def test_129_fix_ip(self):
        # Change the IP address back not to confuse other parts of the testsuite
        old_ip = self.net["unknown0"].usable[-1]
        ip = self.net["unknown0"].usable[15]
        self.dsdb_expect_update("arecord15.aqd-unittest.ms.com", ip=ip)
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def test_130_update_dyndhcp_noop(self):
        ip = self.net["dyndhcp0"].usable[12]
        command = ["update", "address", "--fqdn", self.dynname(ip),
                   "--reverse_ptr", self.dynname(ip)]
        self.noouttest(command)
        self.dsdb_verify(empty=True)

    def test_135_verify_dyndhcp(self):
        ip = self.net["dyndhcp0"].usable[12]
        command = ["show", "fqdn", "--fqdn", self.dynname(ip)]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def test_140_restricted_reverse(self):
        command = ["update", "address",
                   "--fqdn", "arecord17.aqd-unittest.ms.com",
                   "--reverse_ptr", "reverse2.restrict.aqd-unittest.ms.com"]
        out, err = self.successtest(command)
        self.assertEmptyOut(out, command)
        self.matchoutput(err,
                         "WARNING: Will create a reference to "
                         "reverse2.restrict.aqd-unittest.ms.com, but trying to "
                         "resolve it resulted in an error: Name or service "
                         "not known",
                         command)
        self.dsdb_verify(empty=True)

    def test_141_verify_reverse(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord17.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Reverse PTR: reverse2.restrict.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "reverse.restrict.aqd-unittest.ms.com", command)

        command = ["search", "dns", "--record_type", "reserved_name"]
        out = self.commandtest(command)
        self.matchclean(out, "reverse.restrict", command)
        self.matchoutput(out, "reverse2.restrict.aqd-unittest.ms.com", command)

    def test_200_update_dyndhcp(self):
        ip = self.net["dyndhcp0"].usable[12]
        command = ["update", "address", "--fqdn", self.dynname(ip),
                   "--reverse_ptr", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The reverse PTR record cannot be set for DNS "
                         "records used for dynamic DHCP.", command)

    def test_200_ip_conflict(self):
        ip = self.net["unknown0"].usable[14]
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is already used by DNS record "
                         "arecord14.aqd-unittest.ms.com." % ip, command)

    def test_200_update_primary(self):
        command = ["update", "address",
                   "--fqdn", "unittest20.aqd-unittest.ms.com",
                   "--ip", self.net["unknown0"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Record unittest20.aqd-unittest.ms.com is "
                         "a primary name, and its IP address cannot be "
                         "changed.", command)

    def test_200_update_used(self):
        command = ["update", "address",
                   "--fqdn", "unittest20-e1.aqd-unittest.ms.com",
                   "--ip", self.net["unknown0"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Record unittest20-e1.aqd-unittest.ms.com is "
                         "already used by the following interfaces, and its "
                         "IP address cannot be changed: "
                         "unittest20.aqd-unittest.ms.com/eth1.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
