#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016  Contributor
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

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestUpdateAddress(TestBrokerCommand):

    def test_100_update_reverse(self):
        self.dsdb_expect_update("arecord15.aqd-unittest.ms.com",
                                comments="Some address comments")
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord14.aqd-unittest.ms.com",
                   "--comments", "Some address comments"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_verify_arecord15(self):
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Comments: Some address comments", command)
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

    def test_108_clear_comments(self):
        self.dsdb_expect_update("arecord15.aqd-unittest.ms.com",
                                comments="")
        self.noouttest(["update_address",
                        "--fqdn", "arecord15.aqd-unittest.ms.com",
                        "--comments", ""])
        self.dsdb_verify()

    def test_109_verify_comments(self):
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Comments", command)

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
        err = self.statustest(command)
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

    def test145_alias_reverse(self):
        command = ["update", "address",
                   "--fqdn", "arecord17.aqd-unittest.ms.com",
                   "--reverse_ptr", "alias2host.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test146_verify_reverse(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord17.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Reverse PTR: alias2host.aqd-unittest.ms.com",
                         command)

    def test150_address_alias_reverse(self):
        command = ["update", "address",
                   "--fqdn", "arecord17.aqd-unittest.ms.com",
                   "--reverse_ptr", "addralias1.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test151_verify_reverse(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord17.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Reverse PTR: addralias1.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "alias2host.aqd-unittest.ms.com", command)

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
                   "--fqdn", "unittest00.one-nyp.ms.com",
                   "--ip", self.net["unknown0"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Record unittest00.one-nyp.ms.com is "
                         "a primary name, and its IP address cannot be "
                         "changed.", command)

    def test_200_update_srvaddr(self):
        command = ["update", "address",
                   "--fqdn", "unittest20.aqd-unittest.ms.com",
                   "--ip", self.net["unknown0"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record unittest20.aqd-unittest.ms.com is a "
                         "service address, use the update_service_address "
                         "command to change it.",
                         command)

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

    def test_300_update_no_ttl(self):
        command = ["update", "address",
                   "--fqdn", "arecord40.aqd-unittest.ms.com",
                   "--clear_ttl"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)

    def test_320_verify_ttl(self):
        command = ["show", "fqdn", "--fqdn", "arecord40.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "TTL", command)

    def test_330_update_new_ttl(self):
        command = ["update", "address",
                   "--fqdn", "arecord40.aqd-unittest.ms.com",
                   "--ttl", "600"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)

    def test_340_verify_ttl(self):
        command = ["show", "fqdn", "--fqdn", "arecord40.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "TTL: 600", command)

    def test_400_clear_grn(self):
        command = ["update", "address",
                   "--fqdn", "arecord50.aqd-unittest.ms.com",
                   "--clear_grn"]
        self.noouttest(command)

    def test_420_verify_clear_grn(self):
        command = ["show", "fqdn",
                   "--fqdn", "arecord50.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Owned by GRN", command)

    def test_430_update_grn(self):
        command = ["update", "address",
                   "--fqdn", "arecord50.aqd-unittest.ms.com",
                   "--grn", "grn:/ms/ei/aquilon/unittest"]
        self.noouttest(command)

    def test_440_verify_update_grn(self):
        command = ["show", "fqdn",
                   "--fqdn", "arecord50.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest", command)

    def test_450_update_eon_id(self):
        command = ["update", "address",
                   "--fqdn", "arecord51.aqd-unittest.ms.com",
                   "--eon_id", "2"]
        self.noouttest(command)

    def test_460_verify_update_eon_id(self):
        command = ["show", "fqdn",
                   "--fqdn", "arecord51.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
