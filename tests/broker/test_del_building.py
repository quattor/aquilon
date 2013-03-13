#!/usr/bin/env python2.6
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelBuilding(TestBrokerCommand):

    def testdelbu(self):
        self.dsdb_expect("delete_campus_building_aq -campus_name ny "
                         "-building_name bu")
        self.dsdb_expect("delete_building_aq -building bu")
        command = "del building --building bu"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydelbu(self):
        command = "show building --building bu"
        self.notfoundtest(command.split(" "))

    def testdelex(self):
        self.dsdb_expect("delete_building_aq -building cards")
        command = "del building --building cards"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testdelbunotindsdb(self):
        ## add building

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

    def testdelnettest02(self):
        self.dsdb_expect("delete_campus_building_aq -campus_name ny "
                         "-building_name nettest")
        self.dsdb_expect("delete_building_aq -building nettest")
        command = "del building --building nettest"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testdelnettest01(self):
        test_bu = "nettest"

        # add network to building
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--building", test_bu,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete building
        command = "del building --building %s" % test_bu
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete building %s, "
                         "networks were found using this location." % test_bu,
                         command)
        self.dsdb_verify(empty=True)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def test_deletetu(self):
        self.dsdb_expect("delete_campus_building_aq -campus_name ta "
                         "-building_name tu")
        self.dsdb_expect("delete_building_aq -building tu")
        command = "del building --building tu"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_verify_deletetu(self):
        command = "show building --building tu"
        self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
