#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the add/show srv record command."""

import unittest

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddSrvRecord(TestBrokerCommand):

    def test_100_add_kerberos1(self):
        command = ["add", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 88, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_110_add_kerberos2(self):
        command = ["add", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--port", 88, "--priority", 10, "--weight", 20,
                   "--ttl", "3600"]
        self.noouttest(command)

    def test_120_add_kerberos2_dup(self):
        command = ["add", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--port", 88, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "SRV Record _kerberos._tcp.aqd-unittest.ms.com "
                         "already exists.", command)

    def test_130_add_ldap(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_200_show_srvrec(self):
        command = ["show", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _kerberos._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: kerberos", command)
        self.matchoutput(out, "Protocol: tcp", command)
        self.matchoutput(out, "Priority: 10", command)
        self.matchoutput(out, "Weight: 20", command)
        # TODO: emphasize that there are two records
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Target: arecord15.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Port: 88", command)
        self.matchoutput(out, "TTL: 3600", command)
        self.matchclean(out, "Port: 389", command)

    def test_210_search_srvrec(self):
        command = ["search", "dns", "--record_type", "srv"]
        out = self.commandtest(command)
        self.matchoutput(out, "_kerberos._tcp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "_ldap._tcp.aqd-unittest.ms.com", command)
        self.matchclean(out, "alias", command)
        self.matchclean(out, "arecord", command)
        self.matchclean(out, "unittest0", command)

    def test_220_search_bytarget(self):
        command = ["search", "dns", "--target", "arecord14.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _kerberos._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: kerberos", command)
        self.matchoutput(out, "Protocol: tcp", command)
        self.matchoutput(out, "Priority: 10", command)
        self.matchoutput(out, "Weight: 20", command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Port: 88", command)
        self.matchclean(out, "arecord15.aqd-unittest.ms.com", command)

    def test_300_badport(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 0, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The port must be between 1 and 65535.", command)

    def test_310_badprio(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 65536, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The priority must be between 0 and 65535.", command)

    def test_320_badproto(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "badproto", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown protocol badproto.", command)

    def test_330_alias(self):
        command = ["add", "srv", "record", "--service", "ldap-alias",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "alias2host.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_335_search_ldap_alias(self):
        command = ["search", "dns", "--record_type", "srv"]
        out = self.commandtest(command)
        self.matchoutput(out, "_ldap-alias._tcp.aqd-unittest.ms.com", command)

    def test_340_reservedname(self):
        command = ["add", "srv", "record", "--service", "ldap-reserved",
                   "--protocol", "udp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "nyaqd1.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_350_restricted(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "badproto",
                   "--dns_domain", "restrict.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, SRV records are not allowed.",
                         command)

    def test_360_show_missing(self):
        command = ["show", "srv", "record", "--service", "no-such-service",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SRV Record for service no-such-service, protocol "
                         "tcp in DNS domain aqd-unittest.ms.com not found.",
                         command)

    def test_370_restricted_target(self):
        command = ["add", "srv", "record", "--service", "ldap-restrict",
                   "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "ldap.restrict.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.statustest(command)
        self.matchoutput(out,
                         "WARNING: Will create a reference to "
                         "ldap.restrict.aqd-unittest.ms.com, but ",
                         command)

    def test_400_addr_alias_target(self):
        command = ["add", "srv", "record", "--service", "http",
                   "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "addralias1.aqd-unittest.ms.com",
                   "--port", 8080, "--priority", 50, "--weight", 10]
        self.noouttest(command)

    def test_420_show_addr_alias_target(self):
        command = ["show", "srv", "record",
                   "--service", "http",
                   "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _http._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: http", command)
        self.matchoutput(out, "Protocol: tcp", command)
        self.matchoutput(out, "Priority: 50", command)
        self.matchoutput(out, "Weight: 10", command)
        self.matchoutput(out, "Target: addralias1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Port: 8080", command)

    def test_500_grn(self):
        command = ["add", "srv", "record",
                   "--service", "sip", "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord13.aqd-unittest.ms.com",
                   "--port", 5060, "--priority", 10, "--weight", 10,
                   "--grn", "grn:/ms/ei/aquilon/aqd"]
        self.noouttest(command)

    def test_505_verify_grn(self):
        command = ["show", "srv", "record",
                   "--service", "sip", "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_510_implicit_grn(self):
        command = ["add", "srv", "record",
                   "--service", "sip", "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 5060, "--priority", 10, "--weight", 10]
        self.noouttest(command)

    def test_515_verify_implicit_grn(self):
        command = ["search", "dns", "--fullinfo",
                   "--shortname", "_sip._tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_520_eonid(self):
        command = ["add", "srv", "record",
                   "--service", "sip", "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord50.aqd-unittest.ms.com",
                   "--port", 5060, "--priority", 10, "--weight", 10,
                   "--eon_id", "2"]
        self.noouttest(command)

    def test_525_verify_eonid(self):
        command = ["search", "dns", "--fullinfo",
                   "--shortname", "_sip._tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord50.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_530_conflict_of_inconsistent_grn(self):
        command = ["add", "srv", "record",
                   "--service", "sip", "--protocol", "tcp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord51.aqd-unittest.ms.com",
                   "--port", 5060, "--priority", 10, "--weight", 10,
                   "--eon_id", "3"]
        out = self.badrequesttest(command)
        self.searchoutput(out,
                          r"Fqdn _sip._tcp.aqd-unittest.ms.com with target "
                          r"\w+.aqd-unittest.ms.com is set to a different GRN.",
                          command)

    def test_540_grn_conflict_with_primary_name(self):
        command = ["add", "srv", "record",
                   "--service", "sip",
                   "--protocol", "udp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "unittest00.one-nyp.ms.com",
                   "--port", 5060, "--priority", 5, "--weight", 20,
                   "--grn", "grn:/ms/ei/aquilon/unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "SRV Record _sip._udp.aqd-unittest.ms.com depends on "
                         "DNS Record unittest00.one-nyp.ms.com. It conflicts "
                         "with GRN grn:/ms/ei/aquilon/unittest: DNS Record "
                         "unittest00.one-nyp.ms.com is a primary name. GRN "
                         "should not be set but derived from the device.",
                         command)

    def test_550_grn_conflict_with_service_address(self):
        command = ["add", "srv", "record",
                   "--service", "sip",
                   "--protocol", "udp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "zebra2.aqd-unittest.ms.com",
                   "--port", 5060, "--priority", 60, "--weight", 30,
                   "--grn", "grn:/ms/ei/aquilon/unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "SRV Record _sip._udp.aqd-unittest.ms.com depends on "
                         "DNS Record zebra2.aqd-unittest.ms.com. It conflicts "
                         "with GRN grn:/ms/ei/aquilon/unittest: DNS Record "
                         "zebra2.aqd-unittest.ms.com is a service address. GRN "
                         "should not be set but derived from the device.",
                         command)

    def test_560_grn_conflict_with_interface_name(self):
        command = ["add", "srv", "record",
                   "--service", "sip",
                   "--protocol", "udp",
                   "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "unittest20-e1.aqd-unittest.ms.com",
                   "--port", 5060, "--priority", 20, "--weight", 40,
                   "--grn", "grn:/ms/ei/aquilon/unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "SRV Record _sip._udp.aqd-unittest.ms.com depends on "
                         "DNS Record unittest20-e1.aqd-unittest.ms.com. It "
                         "conflicts with GRN grn:/ms/ei/aquilon/unittest: DNS "
                         "Record unittest20-e1.aqd-unittest.ms.com is already "
                         "be used by the interfaces "
                         "unittest20.aqd-unittest.ms.com/eth1. "
                         "GRN should not be set but derived from the device.",
                         command)

    def test_600_add_tls_srvrec(self):
        command = ["add", "srv", "record", "--service", "collab",
                   "--protocol", "tls", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 8080, "--priority", 0, "--weight", 0]
        self.noouttest(command)

    def test_610_show_tls_srvrec(self):
        command = ["show", "srv", "record", "--service", "collab",
                   "--protocol", "tls", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _collab._tls.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: collab", command)
        self.matchoutput(out, "Protocol: tls", command)
        self.matchoutput(out, "Priority: 0", command)
        self.matchoutput(out, "Weight: 0", command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Port: 8080", command)

    def test_700_add_with_dns_env(self):
        command = ["add", "srv", "record", "--service", "collab",
                   "--protocol", "tls", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "addralias1.aqd-unittest-ut-env.ms.com",
                   "--port", 8080, "--priority", 0, "--weight", 0,
                   "--dns_environment", "ut-env"]
        self.noouttest(command)

    def test_710_show_with_dns_env(self):
        command = ["show", "srv", "record", "--service", "collab",
                   "--protocol", "tls", "--dns_domain", "aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _collab._tls.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: collab", command)
        self.matchoutput(out, "Protocol: tls", command)
        self.matchoutput(out, "Priority: 0", command)
        self.matchoutput(out, "Weight: 0", command)
        self.matchoutput(out, "Target: addralias1.aqd-unittest-ut-env.ms.com", command)
        self.matchoutput(out, "Port: 8080", command)
        self.matchoutput(out, "DNS Environment: ut-env", command)

    def test_800_add_with_diff_target_dns_env(self):
        command = ["add", "srv", "record", "--service", "collab2",
                   "--protocol", "tls", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "addralias1.aqd-unittest-ut-env.ms.com",
                   "--port", 2364, "--priority", 20, "--weight", 30,
                   "--dns_environment", "internal",
                   "--target_environment", "ut-env"]
        self.noouttest(command)

    def test_810_show_with_diff_target_dns_env(self):
        command = ["show", "srv", "record", "--service", "collab2",
                   "--protocol", "tls", "--dns_domain", "aqd-unittest.ms.com",
                   "--dns_environment", "internal"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _collab2._tls.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: collab2", command)
        self.matchoutput(out, "Protocol: tls", command)
        self.matchoutput(out, "Priority: 20", command)
        self.matchoutput(out, "Weight: 30", command)
        self.matchoutput(out, "Target: addralias1.aqd-unittest-ut-env.ms.com [environment: ut-env]", command)
        self.matchoutput(out, "Port: 2364", command)
        self.matchoutput(out, "DNS Environment: internal", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddSrvRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
