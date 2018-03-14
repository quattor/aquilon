#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Module for testing the add building command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddBuilding(TestBrokerCommand):

    def test_100_addtu(self):
        self.dsdb_expect("add_building_aq -building_name tu -city ny "
                         "-building_addr 14 Test Lane")
        self.dsdb_expect_add_campus_building("ny", "tu")
        command = ["add", "building", "--building", "tu", "--city", "ny",
                   "--address", "14 Test Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_101_verifyaddtu(self):
        command = "show building --building tu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 14 Test Lane", command)

    def test_102_addhq(self):
        self.dsdb_expect("add_building_aq -building_name hq -city ny "
                         "-building_addr 1585 Broadway, NY, NY 10036")
        self.dsdb_expect_add_campus_building("ny", "hq")
        command = ["add_building", "--building", "hq", "--city", "ny",
                   "--fullname", "seven-fifty",
                   "--address", "1585 Broadway, NY, NY 10036"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_103_addnp(self):
        self.dsdb_expect("add_building_aq -building_name np -city ny "
                         "-building_addr 1 NY Plaza")
        self.dsdb_expect_add_campus_building("ny", "np")
        command = ["add_building", "--building", "np", "--city", "ny",
                   "--fullname", "one-nyp", "--address", "1 NY Plaza"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_104_addoy(self):
        self.dsdb_expect("add_building_aq -building_name oy -city ln "
                         "-building_addr Hounslow, Middlesex")
        self.dsdb_expect_add_campus_building("ln", "oy")
        command = ["add_building", "--building", "oy", "--city", "ln",
                   "--fullname", "heathrow", "--address", "Hounslow, Middlesex"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_addpi(self):
        self.dsdb_expect("add_building_aq -building_name pi -city ny "
                         "-building_addr 1 Pierrepont Plaza")
        self.dsdb_expect_add_campus_building("ny", "pi")
        command = ["add_building", "--building", "pi", "--city", "ny",
                   "--fullname", "pierrepont",
                   "--address", "1 Pierrepont Plaza"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_106_addut(self):
        self.dsdb_expect("add_building_aq -building_name ut -city ny "
                         "-building_addr unittest address")
        self.dsdb_expect_add_campus_building("ny", "ut")
        command = ["add_building", "--building", "ut", "--city", "ny",
                   "--fullname", "Unittest-building",
                   "--address", "unittest address"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_110_addbuinvalid(self):
        command = ["add", "building", "--building", "bu", "--city", "ny",
                   "--address", "12 Cherry Lane", "--uri", "assetinventory://003427"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Location URI not valid: Building name and URI do not match", command)

    def test_111_addbu(self):
        self.dsdb_expect("add_building_aq -building_name bu -city ny "
                         "-building_addr 12 Cherry Lane")
        self.dsdb_expect_add_campus_building("ny", "bu")
        command = ["add", "building", "--building", "bu", "--city", "ny",
                   "--address", "12 Cherry Lane", "--uri", "assetinventory://003428"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_112_verifyaddbu(self):
        command = "show building --building bu"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            Building: bu
              Fullname: bu
              Address: 12 Cherry Lane
              Location URI: assetinventory://003428
              Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny]
            """, command)

    def test_113_addbuforce(self):
        self.dsdb_expect("add_building_aq -building_name fo -city ny "
                         "-building_addr 64 Force Lane")
        self.dsdb_expect_add_campus_building("ny", "fo")
        command = ["add", "building", "--building", "fo", "--city", "ny",
                   "--address", "64 Force Lane", "--uri", "assetinventory://003430",
                   "--force_uri"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_114_verifyaddbuforce(self):
        command = "show building --building fo"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            Building: fo
              Fullname: fo
              Address: 64 Force Lane
              Location URI: assetinventory://003430
              Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny]
            """, command)

    def test_115_addbuincorrecturi(self):
        command = ["add", "building", "--building", "plaza", "--city", "ex",
                   "--address", "Nowhere", "--uri", "incorrect://003427"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Building name and URI do not match", command)

    def test_116_addinvaliduri(self):
        command = ["add", "building", "--building", "plaza", "--city", "ex",
                   "--address", "Nowhere", "--uri", "fakeuri=003427"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "URI 'fakeuri=003427' is not formatted correctly. It must be of the form "
                              "'string://012345' where the number contains 6 digits and is "
                              "zero-padded.", command)

    def test_117_addnocode(self):
        self.dsdb_expect("add_building_aq -building_name Testo -city ln "
                         "-building_addr test address")
        self.dsdb_expect_add_campus_building("ln", "Testo")
        command = ["add", "building", "--building", "Testo", "--city", "ln",
                   "--address", "test address", "--uri", "assetinventory://005555"]
        (out, err) = self.successtest(command)
        self.searchoutput(err, "Warning: 'IT_CODE' in '(.*)' is empty for "
                               "URI 'assetinventory://005555'! Proceeding without validation.", command)

    def test_120_addbucards(self):
        self.dsdb_expect("add_building_aq -building_name cards -city ex "
                         "-building_addr Nowhere")
        self.dsdb_expect_add_campus_building("ta", "cards")
        command = ["add", "building", "--building", "cards", "--city", "ex",
                   "--address", "Nowhere", "--uri", "assetinventory://003427"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_121_verifyaddbucards(self):
        command = "show building --building cards"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            Building: cards
              Fullname: cards
              Address: Nowhere
              Location URI: assetinventory://003427
              Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ta, City ex]
            """, command)

    def test_130_verifyaddbuproto(self):
        command = "show building --building bu --format proto"
        loc = self.protobuftest(command.split(" "), expect=1)[0]
        self.matchoutput(loc.name, "bu", command)
        self.matchoutput(loc.uri, "assetinventory://003428", command)
        self.matchoutput(loc.location_type, "building", command)

    def test_131_verifybuildingall(self):
        command = ["show", "building", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building: ut", command)

    def test_132_verifyshowcsv(self):
        command = "show building --building bu --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "building,bu,city,ny", command)

    def test_133_addnettest(self):
        self.dsdb_expect("add_building_aq -building_name nettest -city ny "
                         "-building_addr Nowhere")
        self.dsdb_expect_add_campus_building("ny", "nettest")
        command = ["add", "building", "--building", "nettest", "--city", "ny",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_134_nonscii(self):
        # Valid UTF-8: a with acute, u with double acute, greek phi
        command = ["add", "building", "--building", "nonascii", "--city", "ny",
                   "--address", "\xc3\xa1\xc5\xb1\xcf\x86"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Only ASCII characters are allowed for --address.",
                         command)

    def test_135_nonutf8(self):
        command = ["add", "building", "--building", "nonascii", "--city", "ny",
                   "--address", "\xe1\xe9\xed\xf3\xfa"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "Value for parameter address is not valid UTF-8",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
