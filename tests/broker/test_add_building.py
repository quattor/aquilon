#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

    def testaddbu(self):
        self.dsdb_expect("add_building_aq -building_name bu -city ny "
                         "-building_addr 12 Cherry Lane")
        self.dsdb_expect_add_campus_building("ny", "bu")
        command = ["add", "building", "--building", "bu", "--city", "ny",
                   "--address", "12 Cherry Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddbu(self):
        command = "show building --building bu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: bu", command)
        self.matchoutput(out, "Address: 12 Cherry Lane", command)

    def testaddbucards(self):
        self.dsdb_expect("add_building_aq -building_name cards -city ex "
                         "-building_addr Nowhere")
        # No campus for city ex
#        self.dsdb_expect_add_campus_building("ny", "bu")
        command = ["add", "building", "--building", "cards", "--city", "ex",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddbucards(self):
        command = "show building --building cards"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: cards", command)
        self.matchoutput(out, "Address: Nowhere", command)

    def testverifyaddbuproto(self):
        command = "show building --building bu --format proto"
        out = self.commandtest(command.split(" "))
        locs = self.parse_location_msg(out, 1)
        self.matchoutput(locs.locations[0].name, "bu", command)
        self.matchoutput(locs.locations[0].location_type, "building", command)

    def testverifybuildingall(self):
        command = ["show", "building", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building: ut", command)

    def testverifyshowcsv(self):
        command = "show building --building bu --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "building,bu,city,ny", command)

    def testaddnettest(self):
        self.dsdb_expect("add_building_aq -building_name nettest -city ny "
                         "-building_addr Nowhere")
        self.dsdb_expect_add_campus_building("ny", "nettest")
        command = ["add", "building", "--building", "nettest", "--city", "ny",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

    def testnonascii(self):
        command = ["add", "building", "--building", "nonascii", "--city", "ny",
                   "--address", "\xe1\xe9\xed\xf3\xfa"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Only ASCII characters are allowed for --address.",
                         command)

    def testnonasciiaudit(self):
        command = ["search", "audit", "--keyword", "nonascii"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"400 aq add_building .*"
                          r"--address='<Non-ASCII value>'",
                          command)
        self.searchoutput(out, r"400 aq add_building .*--building='nonascii'",
                          command)

    def test_addtu(self):
        self.dsdb_expect("add_building_aq -building_name tu -city ny "
                         "-building_addr 14 Test Lane")
        self.dsdb_expect_add_campus_building("ny", "tu")
        command = ["add", "building", "--building", "tu", "--city", "ny",
                   "--address", "14 Test Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_verifyaddtu(self):
        command = "show building --building tu"
        out, err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 14 Test Lane", command)

    def test_addhq(self):
        self.dsdb_expect("add_building_aq -building_name hq -city ny "
                         "-building_addr 1585 Broadway, NY, NY 10036")
        self.dsdb_expect_add_campus_building("ny", "hq")
        command = ["add_building", "--building", "hq", "--city", "ny",
                   "--fullname", "seven-fifty",
                   "--address", "1585 Broadway, NY, NY 10036"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_addnp(self):
        self.dsdb_expect("add_building_aq -building_name np -city ny "
                         "-building_addr 1 NY Plaza")
        self.dsdb_expect_add_campus_building("ny", "np")
        command = ["add_building", "--building", "np", "--city", "ny",
                   "--fullname", "one-nyp", "--address", "1 NY Plaza"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_addoy(self):
        self.dsdb_expect("add_building_aq -building_name oy -city ln "
                         "-building_addr Hounslow, Middlesex")
        self.dsdb_expect_add_campus_building("ln", "oy")
        command = ["add_building", "--building", "oy", "--city", "ln",
                   "--fullname", "heathrow", "--address", "Hounslow, Middlesex"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_addpi(self):
        self.dsdb_expect("add_building_aq -building_name pi -city ny "
                         "-building_addr 1 Pierrepont Plaza")
        self.dsdb_expect_add_campus_building("ny", "pi")
        command = ["add_building", "--building", "pi", "--city", "ny",
                   "--fullname", "pierrepont",
                   "--address", "1 Pierrepont Plaza"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_addut(self):
        self.dsdb_expect("add_building_aq -building_name ut -city ny "
                         "-building_addr unittest address")
        self.dsdb_expect_add_campus_building("ny", "ut")
        command = ["add_building", "--building", "ut", "--city", "ny",
                   "--fullname", "Unittest-building",
                   "--address", "unittest address"]
        self.noouttest(command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
