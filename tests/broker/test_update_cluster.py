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
"""Module for testing the update cluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestUpdateCluster(TestBrokerCommand, PersonalityTestMixin):

    def test_000_add_personalities(self):
        self.create_personality("gridcluster", "hadoop-test",
                                grn="grn:/ms/ei/aquilon/aqd")

    def test_100_updatenoop(self):
        self.noouttest(["update_cluster", "--cluster=utgrid1",
                        "--down_hosts_threshold=2%"])
        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Down Hosts Threshold: 0 (2%)", command)
        self.matchoutput(out, "Maintenance Threshold: 0 (6%)", command)

    def test_1200_updateutgrid1(self):
        command = ["update_cluster", "--cluster=utgrid1",
                   "--down_hosts_threshold=2"]
        self.noouttest(command)

        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Maintenance Threshold: 0 (6%)", command)

    def test_130_update_maint_threshold(self):
        command = ["update_cluster", "--cluster=utgrid1",
                   "--maint_threshold=50%"]
        self.noouttest(command)

        command = "show cluster --cluster utgrid1 --format proto"
        cluster = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(cluster.name, "utgrid1")
        self.assertEqual(cluster.threshold, 2)
        self.assertEqual(cluster.threshold_is_percent, False)
        self.assertEqual(cluster.maint_threshold, 50)
        self.assertEqual(cluster.maint_threshold_is_percent, True)

        command = ["update_cluster", "--cluster=utgrid1",
                   "--maint_threshold=50"]
        self.noouttest(command)

        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Maintenance Threshold: 50", command)

        command = ["update_cluster", "--cluster=utgrid1",
                   "--maint_threshold=0%"]
        self.noouttest(command)

        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Maintenance Threshold: 0 (0%)", command)

    def test_140_updatepersonality(self):
        # Change metacluster personality and revert it.
        command = ["update_cluster", "--cluster", "utgrid1",
                   "--personality", "hadoop-test"]
        self.noouttest(command)

        command = ["show", "cluster", "--cluster", "utgrid1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: hadoop-test", command)

        command = ["update_cluster", "--cluster", "utgrid1",
                   "--personality", "hadoop"]
        self.noouttest(command)

        command = ["show", "cluster", "--cluster", "utgrid1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: hadoop", command)

    def test_150_group_utecl1(self):
        command = ["update_cluster", "--cluster", "utecl1",
                   "--group_with", "utecl2"]
        self.noouttest(command)

    def test_155_verify_group(self):
        command = ["show_cluster", "--cluster", "utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Grouped with ESX Cluster: utecl2", command)

        command = ["show_cluster", "--cluster", "utecl2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Grouped with ESX Cluster: utecl1", command)

        command = ["show_cluster", "--cluster", "utecl2", "--format", "proto"]
        clstr = self.protobuftest(command, expect=1)[0]
        self.assertEqual(len(clstr.grouped_cluster), 1)
        self.assertEqual(clstr.grouped_cluster[0].name, "utecl1")

    def test_160_set_preferred_side(self):
        self.noouttest(["update_cluster", "--cluster", "utbvcs2a",
                        "--preferred_building", "utb2"])

    def test_161_show_utbvcs2a(self):
        command = ["show_cluster", "--cluster", "utbvcs2a"]
        out = self.commandtest(command)
        self.matchoutput(out, "Preferred Building: utb2", command)

    def test_161_cat_utbvcs2a(self):
        command = ["cat", "--cluster", "utbvcs2a", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/cluster/preferred_location/building" = "utb2";',
                         command)

    def test_161_search_preferred(self):
        command = ["search_cluster", "--preferred_building", "utb2"]
        out = self.commandtest(command)
        self.matchoutput(out, "utbvcs2a", command)
        self.matchclean(out, "utbvcs2b", command)
        self.matchclean(out, "utbvcs5", command)

    def test_161_show_all_preferences(self):
        command = ["show_building_preference", "--all"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'^Building Pair: utb1,utb2  Archetype: hacluster  Prefer: utb2\s*'
                          r'Cluster: utbvcs2a  Prefer: utb2$',
                          command)
        self.matchclean(out, "utbvcs2b", command)
        self.matchclean(out, "utbvcs5", command)

    def test_161_search_preferred_archetype(self):
        command = ["search_building_preference", "--archetype", "hacluster"]
        out = self.commandtest(command)
        self.searchoutput(out,
                         r'^Building Pair: utb1,utb2  Archetype: hacluster  Prefer: utb2\s*'
                         r'Cluster: utbvcs2a  Prefer: utb2$',
                         command)

    def test_162_uncluster_preferred(self):
        command = ["uncluster", "--cluster", "utbvcs2a",
                   "--hostname", "utbhost10.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "High Availability Cluster utbvcs2a has "
                         "no members inside preferred building utb2.", command)

    def test_163_flip_side(self):
        self.noouttest(["update_cluster", "--cluster", "utbvcs2a",
                        "--preferred_building", "utb1"])

    def test_164_show_utbvcs2a(self):
        command = ["show_cluster", "--cluster", "utbvcs2a"]
        out = self.commandtest(command)
        self.matchoutput(out, "Preferred Building: utb1", command)

    def test_164_cat_utbvcs2a(self):
        command = ["cat", "--cluster", "utbvcs2a", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/cluster/preferred_location/building" = "utb1";',
                         command)

    def test_166_clear_preferred_side(self):
        self.noouttest(["update_cluster", "--cluster", "utbvcs2a",
                        "--clear_location_preference"])

    def test_167_show_utbvcs2a(self):
        command = ["show_cluster", "--cluster", "utbvcs2a"]
        out = self.commandtest(command)
        self.matchclean(out, "Preferred", command)

    def test_167_cat_utbvcs2a(self):
        command = ["cat", "--cluster", "utbvcs2a", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/cluster/preferred_location/building" = "utb2";',
                         command)

    # TODO: This error condition is currently unreachable due to validating the
    # members' locations first
    #def test_200_preferred_outside_constraint(self):
    #    command = ["update_cluster", "--cluster", "utbvcs2a",
    #               "--preferred_building", "cards"]
    #    out = self.badrequesttest(command)
    #    self.matchoutput(out, "The new preferred location is not inside the "
    #                     "location constraint.", command)

    def test_200_preferred_no_members(self):
        command = ["update_cluster", "--cluster", "utbvcs2a",
                   "--preferred_building", "utb3"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "utbvcs2a has no members inside preferred "
                         "building utb3.", command)

    def test_800_cleanup(self):
        self.drop_personality("gridcluster", "hadoop-test")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
