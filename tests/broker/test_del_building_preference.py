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
"""Module for testing the del_building_preference command"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestDelBuildingPreference(TestBrokerCommand):

    def test_000_justification(self):
        command = ["del_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "The operation has production impact", command)

    def test_100_del_utb12(self):
        command = ["del_building_preference", "--building_pair", "utb1,utb2",
                   "--archetype", "hacluster",
                   "--justification", "tcm=12345678"]
        out = self.statustest(command)
        self.matchoutput(out, "Flushed 4/8 templates", command)

    def test_105_cat_utbvcs2a(self):
        command = ["cat", "--cluster", "utbvcs2a", "--data"]
        out = self.commandtest(command)
        self.matchclean(out, 'system/cluster/preferred_location', command)

    def test_108_make_utbvcs2a(self):
        self.statustest(["make_cluster", "--cluster", "utbvcs2a"])

    # utb2,utb3 is left in place, to be deleted together with the buildings

    def test_110_show_utb12(self):
        command = ["show_building_preference", "--building_pair", "utb2,utb1",
                   "--archetype", "hacluster"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building pair utb1,utb2 does not have a "
                         "preference for archetype hacluster.", command)

    def test_200_single_building(self):
        command = ["del_building_preference", "--building_pair", "ut",
                   "--archetype", "hacluster",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "should be two building codes", command)

    def test_201_three_buildings(self):
        command = ["del_building_preference", "--building_pair", "ut,utb1,utb2",
                   "--archetype", "hacluster",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "should be two building codes", command)

    def test_202_repeated_building(self):
        command = ["del_building_preference", "--building_pair", "ut,ut",
                   "--archetype", "hacluster",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "two different building codes", command)

    def test_210_del_utb12_again(self):
        command = ["del_building_preference", "--building_pair", "utb2,utb1",
                   "--archetype", "hacluster",
                   "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building pair utb1,utb2 does not have a "
                         "preference for archetype hacluster.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelBuildingPreference)
    unittest.TextTestRunner(verbosity=2).run(suite)
