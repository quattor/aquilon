#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2015,2016,2017  Contributor
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
"""Module for testing the update srv record command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateSrvRecord(TestBrokerCommand):

    def test_100_update(self):
        command = ["update", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--weight", 15, "--priority", 25, "--port", "8888",
                   "--comments", "New SRV record comments"] + self.valid_just_tcm
        self.noouttest(command)

    def test_200_verify(self):
        command = ["search", "dns", "--fullinfo", "--record_type", "srv",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Weight: 15", command)
        self.matchoutput(out, "Priority: 25", command)
        self.matchoutput(out, "Port: 8888", command)
        self.matchoutput(out, "Comments: New SRV record comments", command)

    def test_300_missing(self):
        command = ["update", "srv", "record", "--service", "no-such-service",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--weight", 15, "--priority", 25, "--port", "8888",
                   "--comments", "New SRV record comments"] + self.valid_just_tcm
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SRV Record _no-such-service._tcp.aqd-unittest.ms.com, "
                         "DNS environment internal not found.",
                         command)

    def test_400_update_ttl(self):
        command = ["update", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--ttl", 1800] + self.valid_just_tcm
        self.noouttest(command)

    def test_420_verify(self):
        command = ["search", "dns", "--fullinfo", "--record_type", "srv",
                   "--target", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "TTL: 1800", command)

    def test_500_clear_ttl(self):
        command = ["update", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--clear_ttl"] + self.valid_just_tcm
        self.noouttest(command)

    def test_520_verify(self):
        command = ["search", "dns", "--fullinfo", "--record_type", "srv",
                   "--target", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "TTL", command)

    def test_600_update_grn(self):
        command = ["update", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--grn", "grn:/ms/ei/aquilon/unittest"] + self.valid_just_tcm
        self.noouttest(command)

    def test_605_verify_update_grn(self):
        command = ["show", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Owned by GRN: grn:/ms/ei/aquilon/unittest",
                         command)
        self.matchclean(out,
                        "Owned by GRN: grn:/ms/ei/aquilon/aqd",
                        command)

    def test_610_clear_grn(self):
        command = ["update", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--clear_grn"] + self.valid_just_tcm
        self.noouttest(command)

    def test_615_verify_clear_grn(self):
        command = ["show", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out,
                        "Owned by GRN: grn:/ms/ei/aquilon/aqd",
                        command)

    def test_620_update_eon_id(self):
        command = ["update", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--eon_id", "2"] + self.valid_just_tcm
        self.noouttest(command)

    def test_625_verify_update_grn(self):
        command = ["show", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Owned by GRN: grn:/ms/ei/aquilon/aqd",
                         command)
        self.matchclean(out,
                        "Owned by GRN: grn:/ms/ei/aquilon/unittest",
                        command)

    def test_630_update_grn_with_target(self):
        command = ["update", "srv", "record", "--service", "sip",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord50.aqd-unittest.ms.com",
                   "--grn", "grn:/ms/ei/aquilon/unittest"] + self.valid_just_tcm
        out = self.badoptiontest(command)
        self.matchoutput(out,
                         "Option or option group grn conflicts with target",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateSrvRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
