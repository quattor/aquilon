#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the update archetype command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand


class TestUpdateAlias(TestBrokerCommand):

    def test_100_update(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_110_update_mscom(self):
        command = ["update", "alias", "--fqdn", "alias.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--comments", "New alias comments"]
        self.dsdb_expect("update_host_alias "
                         "-alias alias.ms.com "
                         "-new_host arecord14.aqd-unittest.ms.com "
                         "-new_comments New alias comments")
        self.noouttest(command)
        self.dsdb_verify()

    def test_200_missing_target(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host.aqd-unittest.ms.com",
                   "--target", "no-such-name.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Target FQDN no-such-name.aqd-unittest.ms.com "
                         "does not exist in DNS environment internal.",
                         command)

    def test_210_not_an_alias(self):
        command = ["update", "alias",
                   "--fqdn", "arecord13.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Alias arecord13.aqd-unittest.ms.com not found.",
                         command)

    def test_300_verify_alias(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias2host.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)

    def test_310_verify_mscom(self):
        command = ["search", "dns", "--fullinfo", "--fqdn", "alias.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Comments: New alias comments", command)

    def test_320_verify_oldtarget(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord13.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchclean(out, "alias.ms.com", command)

    def test_330_verify_newtarget(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Aliases: alias.ms.com, "
                         "alias2alias.aqd-unittest.ms.com, "
                         "alias2host.aqd-unittest.ms.com", command)

    def test_400_repoint_restrict1(self):
        command = ["update", "alias", "--fqdn", "restrict1.aqd-unittest.ms.com",
                   "--target", "target2.restrict.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "WARNING: Will create a reference to "
                         "target2.restrict.aqd-unittest.ms.com, but ",
                         command)

    def test_410_verify_target(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'Aliases: restrict2.aqd-unittest.ms.com$',
                          command)

    def test_410_verify_target2(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target2.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'Aliases: restrict1.aqd-unittest.ms.com$',
                          command)

    def test_420_repoint_restrict2(self):
        command = ["update", "alias", "--fqdn", "restrict2.aqd-unittest.ms.com",
                   "--target", "target2.restrict.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_430_verify_target_gone(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target.restrict.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_430_verify_target2(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target2.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Aliases: restrict1.aqd-unittest.ms.com, "
                         "restrict2.aqd-unittest.ms.com",
                         command)

    def test_500_repoint2diff_environment(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host.aqd-unittest-ut-env.ms.com",
                   "--dns_environment", "ut-env",
                   "--target", "alias13.aqd-unittest.ms.com",
                   "--target_environment", "ut-env"]
        self.noouttest(command)

    def test_505_verify_alias_repoint2diff_environment(self):
        command = ["show", "alias",
                   "--fqdn", "alias2host.aqd-unittest-ut-env.ms.com",
                   "--dns_environment", "ut-env"]
        out = self.commandtest(command)

        self.matchoutput(out, "Alias: alias2host.aqd-unittest-ut-env.ms.com", command)
        self.matchoutput(out, "Target: alias13.aqd-unittest.ms.com", command)
        self.matchoutput(out, "DNS Environment: ut-env", command)

    def test_600_update_ttl(self):
        command = ["update", "alias",
                   "--fqdn", "alias2alias.aqd-unittest.ms.com",
                   "--ttl", 120]
        self.noouttest(command)

    def test_620_verify_update_ttl(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias2alias.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Alias: alias2alias.aqd-unittest.ms.com", command)
        self.matchoutput(out, "TTL: 120", command)

    def test_700_remove_ttl(self):
        command = ["update", "alias",
                   "--fqdn", "alias2alias.aqd-unittest.ms.com",
                   "--clear_ttl"]
        self.noouttest(command)

    def test_720_verify_remove_ttl(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias2alias.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "TTL", command)

    def test_800_update_grn(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host-grn.aqd-unittest.ms.com",
                   "--grn", "grn:/ms/ei/aquilon/unittest"]
        self.noouttest(command)

    def test_805_verify_update_grn(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias2host-grn.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest",
                         command)

    def test_810_update_eon_id(self):
        command = ["update", "alias",
                   "--fqdn", "alias3alias.aqd-unittest.ms.com",
                   "--eon_id", "2"]
        self.noouttest(command)

    def test_815_verify_update_eon_id(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias3alias.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd",
                         command)

    def test_816_grn_conflict_with_multi_level_alias(self):
        command = ["update", "alias",
                   "--fqdn", "alias2alias.aqd-unittest.ms.com",
                   "--target", "unittest00.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Alias alias2alias.aqd-unittest.ms.com "
                         "is assoicated with GRN grn:/ms/ei/aquilon/aqd. "
                         "It conflicts with target "
                         "DNS Record unittest00.one-nyp.ms.com: "
                         "DNS Record unittest00.one-nyp.ms.com is a "
                         "primary name. GRN should not be set but derived "
                         "from the device.",
                         command)

    def test_820_clear_grn(self):
        command = ["update", "alias",
                   "--fqdn", "alias3alias.aqd-unittest.ms.com",
                   "--clear_grn"]
        self.noouttest(command)

    def test_825_verify_clear_grn(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias3alias.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Owned by GRN:", command)

    def test_830_update_grn_conflict(self):
        command = ["add", "alias",
                   "--fqdn", "temp-alias.aqd-unittest.ms.com",
                   "--target", "unittest00.one-nyp.ms.com"]
        self.noouttest(command)

        command = ["update", "alias",
                   "--fqdn", "temp-alias.aqd-unittest.ms.com",
                   "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Alias temp-alias.aqd-unittest.ms.com depends on "
                         "DNS Record unittest00.one-nyp.ms.com. "
                         "It conflicts with GRN grn:/ms/ei/aquilon/aqd: "
                         "DNS Record unittest00.one-nyp.ms.com is a "
                         "primary name. GRN should not be set but derived "
                         "from the device.",
                         command)

        command = ["del", "alias",
                   "--fqdn", "temp-alias.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_835_grn_conflict_with_primary_name(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host-grn.aqd-unittest.ms.com",
                   "--target", "unittest00.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Alias alias2host-grn.aqd-unittest.ms.com "
                         "is assoicated with GRN grn:/ms/ei/aquilon/unittest. "
                         "It conflicts with target "
                         "DNS Record unittest00.one-nyp.ms.com: "
                         "DNS Record unittest00.one-nyp.ms.com is a "
                         "primary name. GRN should not be set but derived "
                         "from the device.",
                         command)

    def test_840_grn_conflict_with_service_address(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host-grn.aqd-unittest.ms.com",
                   "--target", "zebra2.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Alias alias2host-grn.aqd-unittest.ms.com "
                         "is assoicated with GRN grn:/ms/ei/aquilon/unittest. "
                         "It conflicts with target "
                         "DNS Record zebra2.aqd-unittest.ms.com: "
                         "DNS Record zebra2.aqd-unittest.ms.com is a "
                         "service address. GRN should not be set but derived "
                         "from the device.",
                         command)

    def test_850_grn_conflict_with_interface_name(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host-grn.aqd-unittest.ms.com",
                   "--target", "unittest20-e1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Alias alias2host-grn.aqd-unittest.ms.com "
                         "is assoicated with GRN grn:/ms/ei/aquilon/unittest. "
                         "It conflicts with target "
                         "DNS Record unittest20-e1.aqd-unittest.ms.com: "
                         "DNS Record unittest20-e1.aqd-unittest.ms.com is "
                         "already be used by the interfaces "
                         "unittest20.aqd-unittest.ms.com/eth1. "
                         "GRN should not be set but derived from the device.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
