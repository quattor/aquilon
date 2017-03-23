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
"""Demolish the infrastructure used for testing HA clusters"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin

from .test_build_clusters import config, host_fqdn, reset_config

class TestDemolishClusters(MachineTestMixin, TestBrokerCommand):

    @classmethod
    def setUpClass(cls):
        """ Fill in the computed bits of config dict prior to test execution """
        super(TestDemolishClusters, cls).setUpClass()
        reset_config()

    def test_100_uncluster(self):
        """ Remove hosts from clusters that were added for the use case """
        for host, params in config["host"].items():
            self.noouttest(["uncluster", "--cluster", params["cluster"],
                            "--hostname", host_fqdn(host)])

    def test_110_del_cluster(self):
        """ Remove clusters that were added for the use case """
        for cluster in config["cluster"]:
            self.statustest(["del_cluster", "--cluster", cluster])

    def test_120_del_host(self):
        """ Remove hosts that were added for the use case """
        for host in config["host"]:
            args = config["host"][host]
            self.delete_host(host_fqdn(host), config["ip"][host],
                             args["machine"])

    def test_130_del_rack(self):
        """ Remove racks that were added for the use case """
        for rack in config["rack"]:
            self.noouttest(["del_rack", "--rack", rack])

    def test_140_pre_condition(self):
        # This pair should still exist, and should be gone with the buildings
        command = ["show_building_preference", "--building_pair", "utb2,utb3",
                   "--archetype", "hacluster"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building Pair: utb2,utb3", command)

    def test_141_del_building(self):
        """ Remove buildings that were added for the use case """
        for building in config["building"]:
            self.dsdb_expect_del_campus_building("ny", building)
            self.dsdb_expect("delete_building_aq -building %s" % building)
            self.noouttest(["del_building", "--building", building])
            self.dsdb_verify()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDemolishClusters)
    unittest.TextTestRunner(verbosity=2).run(suite)
