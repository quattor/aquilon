#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the update building command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateBuilding(TestBrokerCommand):

    def test_100_addbu(self):
        self.dsdb_expect("add_building_aq -building_name tu -city ny "
                         "-building_addr 14 Test Lane")
        self.dsdb_expect("add_campus_building_aq -campus_name ny "
                         "-building_name tu")
        command = ["add", "building", "--building", "tu", "--city", "ny",
                   "--address", "14 Test Lane"]
        out, err = self.successtest(command)

        self.matchoutput(err, "Action: adding new building tu to DSDB.",
                         command)
        self.matchoutput(err, "Action: adding building tu to campus ny "
                         "in DSDB.", command)
        self.dsdb_verify()

    def test_101_verifyaddbu(self):
        command = "show building --building tu"
        out, err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 14 Test Lane", command)

    def test_102_updateaddress(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 24 Cherry Lane")
        command = ["update", "building", "--building", "tu",
                   "--address", "24 Cherry Lane"]
        out, err = self.successtest(command)
        self.matchoutput(err, "Action: set address of building tu to 24 "
                         "Cherry Lane in DSDB.", command)
        self.dsdb_verify()

    def test_103_verifyupdateaddress(self):
        command = "show building --building tu"
        out, err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 24 Cherry Lane", command)

    def test_104_updatecitybad(self):
        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "ln"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Bad Request: Cannot change hubs. City ln is in "
                         "Hub ln while Building tu is in Hub ny.",
                         command)

    def test_105_adde5city(self):
        self.noouttest(["map", "service", "--city", "ny",
                        "--service", "afs", "--instance", "q.ny.ms.com"])

    def test_106_updatecity(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 20 Penny Lane")
        self.dsdb_expect("delete_campus_building_aq -campus_name ny "
                         "-building_name tu")
        self.dsdb_expect("add_campus_building_aq -campus_name ta "
                         "-building_name tu")

        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "e5"]
        err = self.statustest(command)
        self.matchoutput(err, "There are 2 service(s) mapped to the "
                         "old location of the (city ny), "
                         "please review and manually update mappings for "
                         "the new location as needed.", command)

        self.matchoutput(err, "Action: set address of building tu to 20 "
                         "Penny Lane in DSDB.", command)
        self.matchoutput(err, "Action: removing building tu from campus ny in "
                         "DSDB.", command)
        self.matchoutput(err, "Action: adding building tu to campus ta in "
                         "DSDB.", command)

        self.dsdb_verify()

    def test_107_verifyupdatecity(self):
        command = "show building --building tu"
        out,err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 20 Penny Lane", command)
        self.matchoutput(out, "City e5", command)

    def test_108_delte(self):
        self.dsdb_expect("delete_campus_building_aq -campus_name ta "
                         "-building_name tu")
        self.dsdb_expect("delete_building_aq -building tu")
        command = "del building --building tu"
        out,err = self.successtest(command.split(" "))

        self.matchoutput(err, "Action: removing building tu from campus ta in "
                         "DSDB.", command)
        self.matchoutput(err, "Action: removing building tu from DSDB.",
                         command)
        self.dsdb_verify()

    def test_109_verifydelete(self):
        command = "show building --building tu"
        self.notfoundtest(command.split(" "))

    def test_110_unmapafs(self):
        self.noouttest(["unmap", "service", "--city", "ny",
                        "--service", "afs", "--instance", "q.ny.ms.com"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
