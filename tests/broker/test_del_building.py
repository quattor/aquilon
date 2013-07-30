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
"""Module for testing the del building command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelBuilding(TestBrokerCommand):

    def test_100_del_bu(self):
        self.dsdb_expect_del_campus_building("ny", "bu")
        self.dsdb_expect("delete_building_aq -building bu")
        command = "del building --building bu"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_100_del_ex(self):
        self.dsdb_expect("delete_building_aq -building cards")
        command = "del building --building cards"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_100_del_tu(self):
        self.dsdb_expect_del_campus_building("ta", "tu")
        self.dsdb_expect("delete_building_aq -building tu")
        command = "del building --building tu"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_110_del_bunotindsdb(self):
        test_building = "bz"
        self.dsdb_expect("add_building_aq -building_name bz -city ex "
                         "-building_addr Nowhere")
        command = ["add", "building", "--building", test_building, "--city", "ex",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

        dsdb_command = "delete_building_aq -building %s" % test_building
        errstr = "bldg %s doesn't exists" % test_building
        self.dsdb_expect(dsdb_command, True, errstr)
        command = "del building --building %s" % test_building
        out, err = self.successtest(command.split(" "))
        self.matchoutput(err,
                         "DSDB does not have building bz defined, proceeding.",
                         command)
        self.dsdb_verify()

    def test_120_add_nettest_net(self):
        self.net.allocate_network(self, "nettest_net", 24, "unknown",
                                  "building", "nettest",
                                  comments="Made-up network")

    def test_121_del_nettest_fail(self):
        # try delete building
        command = "del building --building nettest"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete building nettest, "
                         "networks were found using this location.",
                         command)
        self.dsdb_verify(empty=True)

    def test_122_cleanup_nettest_net(self):
        self.net.dispose_network(self, "nettest_net")

    def test_130_del_nettest(self):
        self.dsdb_expect_del_campus_building("ny", "nettest")
        self.dsdb_expect("delete_building_aq -building nettest")
        command = "del building --building nettest"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_200_del_building_notexist(self):
        command = "del building --building building-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Building building-does-not-exist not found.",
                         command)

    def test_300_verify_bu(self):
        command = "show building --building bu"
        self.notfoundtest(command.split(" "))

    def test_300_verify_tu(self):
        command = "show building --building tu"
        self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
