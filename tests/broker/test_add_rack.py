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
"""Module for testing the add rack command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRack(TestBrokerCommand):

    def test_100_addut3(self):
        command = "add rack --fullname ut3 --bunker zebrabucket.ut --row a --column 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3", command)
        command = "show building --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Next Rack ID: 4", command)

    def test_101_addut3again(self):
        command = "update building --building ut --next_rackid 3"
        out = self.commandtest(command.split(" "))
        command = "add rack --fullname ut3 --room utroom1 --row a --column 3"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Rack ut3 already exists.", command)
        command = "update building --building ut --next_rackid 4"
        out = self.commandtest(command.split(" "))

    def test_105_verifyaddut3(self):
        command = "show rack --rack ut3"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            Rack: ut3
              Fullname: ut3
              Row: a
              Column: 3
              Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny, Building ut, Room utroom1, Bunker zebrabucket.ut]
            """, command)

    def test_110_verifyaddut3proto(self):
        command = "show rack --rack ut3 --format proto"
        loc = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(loc.name, "ut3")
        self.assertEqual(loc.location_type, "rack")
        self.assertEqual(loc.row, "a")
        self.assertEqual(loc.col, "3")

    def test_115_addcards1(self):
        command = "add rack --fullname cards1 --building cards --row a --column 1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "cards1", command)

    def test_120_verifyaddcards1(self):
        command = "show rack --rack cards1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: cards1", command)
        self.matchoutput(out, "Row: a", command)
        self.matchoutput(out, "Column: 1", command)

    def test_125_addnp3(self):
        command = "add rack --fullname np3 --bunker zebrabucket.np --row a --column 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np3", command)

    def test_130_addut4(self):
        command = "add rack --fullname A4 --room utroom1 --row a --column 4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut4", command)

    def test_135_addut8(self):
        # Test override rackid
        command = "add rack --fullname 8.6.7 --building ut --row g --column 2 --force_rackid ut8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut8", command)

    def test_140_addut9(self):
        # Test that next rackid for building ut was reset to 8 + 1,
        # because force_rackid with value > current next_rackid was used
        command = "add rack --fullname Aperture_name --bunker bucket2.ut --row g --column 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut9", command)

    def test_145_verifyut9(self):
        command = "show rack --rack ut9"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Fullname: Aperture_name", command)
        self.matchoutput(out,
                         "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus ny, City ny, "
                         "Building ut, Room utroom2, Bunker bucket2.ut]",
                         command)

    def test_146_test_fillin_gaps(self):
        # Test that next rackid for building ut was NOT reset,
        # because force_rackid with value < current next_rackid was used
        command = "add rack --fullname Aperture_name --building ut --row g --column 6 --force_rackid ut6"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut6", command)
        command = "show building --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Next Rack ID: 10", command)

    def test_147_test_fillin_gaps_delete(self):
        command = "del rack --rack ut6"
        self.noouttest(command.split(" "))

    def test_148_add_rack_fail_name_format(self):
        command = "add rack --force_rackid ut12-66-1 --building ut --row g --column 4"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err, "Invalid rack name ut12-66-1. Correct name format: "
                              "building name + numeric rack ID.", command)

    def test_149_add_rack_fail_option(self):
        command = "add rack --rackid ut12-66-1 --building ut --row g --column 4"
        err = self.badoptiontest(command.split(" "))
        self.matchoutput(err, "no such option: --rackid", command)

    def test_150_addut10(self):
        command = "add rack --building ut --row g --column 4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut10", command)

    def test_155_addut11(self):
        # Test that if next_rackid == force_rackid this next_rackid is incremented by 1
        command = "add rack --bunker zebrabucket.ut --row k --column 1 --force_rackid ut11"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut11", command)
        command = "show building --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Next Rack ID: 12", command)

    def test_160_addut12(self):
        command = "add rack --building ut --row k --column 2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut12", command)

    def test_165_addnp7(self):
        command = "update building --building np --next_rackid 7"
        out = self.commandtest(command.split(" "))
        command = "add rack --building np --row g --column 1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np7", command)

    def test_170_addnp997(self):
        command = "update building --building np --next_rackid 997"
        out = self.commandtest(command.split(" "))
        command = "add rack --building np --row ZZ --column 99"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np997", command)

    def test_175_addnp998(self):
        command = "add rack --building np --row yy --column 88"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np998", command)

    def test_180_addnp999(self):
        command = "add rack --building np --row zz --column 11"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np999", command)

    def test_185_addut13(self):
        command = "add rack --building ut --row k --column 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut13", command)

    def test_190_addnp13(self):
        command = "update building --building np --next_rackid 13"
        out = self.commandtest(command.split(" "))
        command = "add rack --building np --row k --column 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np13", command)

    def test_195_addut14(self):
        command = "add rack --bunker zebrabucket.ut --row k --column 4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut14", command)

    def test_200_verifyaddnp997(self):
        command = "show rack --rack np997"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np997", command)
        self.matchoutput(out, "Row: zz", command)
        self.matchoutput(out, "Column: 99", command)

    def test_205_addnewalphanumericrack(self):
        command = "update building --building np --next_rackid 909"
        out = self.commandtest(command.split(" "))
        command = "add rack --building np --row 99 --column zz"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np909", command)

    def test_210_verifynp909(self):
        command = "show rack --rack np909"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np909", command)
        self.matchoutput(out, "Row: 99", command)
        self.matchoutput(out, "Column: zz", command)

    def test_215_verifyshowallcsv(self):
        command = "show rack --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "rack,ut3,bunker,zebrabucket.ut,a,3", command)
        self.matchoutput(out, "rack,ut4,room,utroom1,a,4", command)
        self.matchoutput(out, "rack,np997,building,np,zz,99", command)
        self.matchoutput(out, "rack,np909,building,np,99,zz", command)

    def test_220_dsdbfailure(self):
        command = "update building --building ut --next_rackid 666"
        out = self.commandtest(command.split(" "))
        command = "add rack --building ut --row 666 --column zz"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err, "Rack ut666 is already defined", command)
        self.matchoutput(err, "DSDB command failed: add_rack", command)
        self.matchoutput(err, "Bad Request: DSDB update failed", command)

    def test_225_dsdbfailureoy604(self):
        command = "add rack --building oy --row 604 --column zz"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err, "Rack oy604 is already defined", command)
        self.matchoutput(err, "Bad Request: DSDB update failed", command)
        self.matchoutput(err, "DSDB command failed: add_rack", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRack)
    unittest.TextTestRunner(verbosity=2).run(suite)
