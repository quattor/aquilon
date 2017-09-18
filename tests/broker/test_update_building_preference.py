#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017  Contributor
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
"""Module for testing the update_building_preference command"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestUpdateBuildingPreference(TestBrokerCommand):

    def test_000_justification(self):
        command = ["update_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "utb1"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

    def test_100_update_utb12(self):
        command = ["update_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "utb1"] + self.valid_just_tcm
        out = self.statustest(command)
        self.matchoutput(out, "Flushed 4/8 templates.", command)

    def test_105_show_utb12(self):
        command = ["show_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Building Pair: utb1,utb2  Archetype: hacluster  Prefer: utb1
            """, command)

    def test_105_show_utb12_proto(self):
        # Different pair order
        command = ["show_building_preference", "--building_pair", "utb2,utb1",
                   "--archetype", "hacluster", "--format", "proto"]
        pref = self.protobuftest(command, expect=1)[0]
        self.assertEqual(len(pref.location), 2)
        self.assertEqual(pref.location[0].location_type, "building")
        self.assertEqual(pref.location[0].name, "utb1")
        self.assertEqual(pref.location[1].location_type, "building")
        self.assertEqual(pref.location[1].name, "utb2")
        self.assertEqual(pref.prefer.location_type, "building")
        self.assertEqual(pref.prefer.name, "utb1")
        # TODO
        #self.assertEqual(pref.archetype.name, "hacluster")

    def test_105_cat_utbvcs2a(self):
        command = ["cat", "--cluster", "utbvcs2a", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/cluster/preferred_location/building" = "utb1";',
                         command)

    def test_106_show_building_preference_utbvcs2a(self):
        command = ["show_building_preference", "--cluster", "utbvcs2a"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'Building Pair: utb1,utb2  Archetype: hacluster  Prefer: utb1',
                         command)

    def test_108_make_utbvcs2a(self):
        self.statustest(["make_cluster", "--cluster", "utbvcs2a"])

    def test_200_single_building(self):
        command = ["update_building_preference", "--building_pair", "ut",
                   "--archetype", "hacluster", "--prefer", "ut"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "should be two building codes", command)

    def test_201_three_buildings(self):
        command = ["update_building_preference", "--building_pair", "ut,utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "ut"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "should be two building codes", command)

    def test_202_repeated_building(self):
        command = ["update_building_preference", "--building_pair", "ut,ut",
                   "--archetype", "hacluster", "--prefer", "ut"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "two different building codes", command)

    def test_203_preferred_outside(self):
        command = ["update_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "ut"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Preferred building ut must be one of "
                         "utb1 and utb2.", command)

    def test_210_update_missing_pair(self):
        command = ["update_building_preference", "--building_pair", "utb1,utb3",
                   "--archetype", "hacluster", "--prefer", "utb3"] + self.valid_just_tcm
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building pair utb1,utb3 does not have a "
                         "preference for archetype hacluster.", command)

    def test_210_update_missing_archetype(self):
        command = ["update_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "esx_cluster", "--prefer", "utb2"] + self.valid_just_tcm
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building pair utb1,utb2 does not have a "
                         "preference for archetype esx_cluster.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateBuildingPreference)
    unittest.TextTestRunner(verbosity=2).run(suite)
