#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
"""Module for testing the add_building_preference command"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestAddBuildingPreference(TestBrokerCommand):

    def test_000_justification(self):
        command = ["add_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "utb2"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "The operation has production impact", command)

    def test_100_add_utb12(self):
        command = ["add_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "utb2",
                   "--justification", "tcm=12345678"]
        out = self.statustest(command)
        self.matchoutput(out, "Flushed 4/8 templates.", command)

    def test_105_show_utb12(self):
        command = ["show_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Building Pair: utb1,utb2 Archetype: hacluster
              Preferred Building: utb2
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
        self.assertEqual(pref.prefer.name, "utb2")
        # TODO
        #self.assertEqual(pref.archetype.name, "hacluster")

    def test_105_cat_utbvcs2a(self):
        command = ["cat", "--cluster", "utbvcs2a", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/cluster/preferred_location/building" = "utb2";',
                         command)

    def test_105_cat_utbvcs5a(self):
        command = ["cat", "--cluster", "utbvcs5a", "--data"]
        out = self.commandtest(command)
        self.matchclean(out, "preferred_location", command)

    def test_105_show_utvcs2a(self):
        command = ["show_cluster", "--cluster", "utbvcs2a"]
        out = self.commandtest(command)
        # No override
        self.matchclean(out, "Preferred", command)

    def test_108_make_utbvcs2a(self):
        self.statustest(["make_cluster", "--cluster", "utbvcs2a"])

    def test_110_add_utb23(self):
        # The pair is not given in lexicographical order; add some whitespace,
        # too
        command = ["add_building_preference", "--building_pair", "utb3, utb2 ",
                   "--archetype", "hacluster", "--prefer", "utb2",
                   "--justification", "tcm=12345678"]
        out = self.statustest(command)
        self.matchoutput(out, "Flushed 6/10 templates.", command)

    def test_200_single_building(self):
        command = ["add_building_preference", "--building_pair", "ut",
                   "--archetype", "hacluster", "--prefer", "ut",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "should be two building codes", command)

    def test_201_three_buildings(self):
        command = ["add_building_preference", "--building_pair", "ut,utb1,utb2",
                   "--archetype", "hacluster", "--prefer", "ut",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "should be two building codes", command)

    def test_202_repeated_building(self):
        command = ["add_building_preference", "--building_pair", "ut,ut",
                   "--archetype", "hacluster", "--prefer", "ut",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "two different building codes", command)

    def test_203_preferred_outside(self):
        command = ["add_building_preference", "--building_pair", "utb1,utb3",
                   "--archetype", "hacluster", "--prefer", "ut",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Preferred building ut must be one of "
                         "utb1 and utb3.", command)

    def test_210_add_utb12_again(self):
        command = ["add_building_preference", "--building_pair", "utb2,utb1",
                   "--archetype", "hacluster", "--prefer", "utb2",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Building pair utb1,utb2 already has a "
                         "preference for archetype hacluster.", command)

    def test_220_bad_archetype(self):
        command = ["add_building_preference", "--building_pair", "utb2,utb1",
                   "--archetype", "aquilon", "--prefer", "utb2",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Archetype aquilon is not a cluster archetype.",
                         command)

    def test_220_bad_archetype_show(self):
        command = ["show_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "esx_cluster"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building pair utb1,utb2 does not have a "
                         "preference for archetype esx_cluster.", command)

    def test_300_show_building_preference_all(self):
        command = ["show_building_preference", "--all"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Building Pair: utb1,utb2 Archetype: hacluster
              Preferred Building: utb2
            Building Pair: utb2,utb3 Archetype: hacluster
              Preferred Building: utb2
            """, command)

    def test_300_search_building(self):
        command = ["search_building_preference", "--building", "utb2"]
        out = self.commandtest(command)
        self.matchoutput(out, "utb1,utb2,hacluster", command)
        self.matchoutput(out, "utb2,utb3,hacluster", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBuildingPreference)
    unittest.TextTestRunner(verbosity=2).run(suite)
