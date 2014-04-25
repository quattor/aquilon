#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
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

    def test_200_updateutgrid1(self):
        command = ["update_cluster", "--cluster=utgrid1",
                   "--down_hosts_threshold=2"]
        self.noouttest(command)

        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Maintenance Threshold: 0 (6%)", command)

    def test_300_update_maint_threshold(self):
        command = ["update_cluster", "--cluster=utgrid1",
                   "--maint_threshold=50%"]
        self.noouttest(command)

        command = "show cluster --cluster utgrid1 --format proto"
        out = self.commandtest(command.split(" "))
        cluslist = self.parse_clusters_msg(out)
        cluster = cluslist.clusters[0]
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

    def test_400_updatepersonality(self):
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

    def test_800_cleanup(self):
        self.drop_personality("gridcluster", "hadoop-test")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
