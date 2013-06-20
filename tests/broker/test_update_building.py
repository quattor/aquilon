#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Module for testing the update building command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateBuilding(TestBrokerCommand):

    def test_102_updateaddress(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 24 Cherry Lane")
        command = ["update", "building", "--building", "tu",
                   "--address", "24 Cherry Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_103_verifyupdateaddress(self):
        command = "show building --building tu"
        out, err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 24 Cherry Lane", command)

    def test_104_updatecitybad(self):
        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "ln"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Bad Request: Cannot change hubs. City ln is in "
                         "Hub ln while Building tu is in Hub ny.",
                         command)

    def test_106_updatecity(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 20 Penny Lane")
        self.dsdb_expect_del_campus_building("ny", "tu")
        self.dsdb_expect_add_campus_building("ta", "tu")

        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "e5"]
        err = self.statustest(command)
        self.matchoutput(err, "There are 1 service(s) mapped to the "
                         "old location of the (city ny), "
                         "please review and manually update mappings for "
                         "the new location as needed.", command)
        self.dsdb_verify()

    def test_107_verifyupdatecity(self):
        command = "show building --building tu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 20 Penny Lane", command)
        self.matchoutput(out, "City e5", command)

    def test_110_update_ut_dnsdomain(self):
        command = ["update", "building", "--building", "ut",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_115_verify_ut_dnsdomain(self):
        command = ["show", "building", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_110_update_tu_dnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_115_verify_tu_dnsdomain(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_120_update_tu_nodnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", ""]
        self.noouttest(command)

    def test_125_verify_tu_dnsdomain_gone(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchclean(out, "Default DNS Domain", command)
        self.matchclean(out, "aqd-unittest.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
