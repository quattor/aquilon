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
"""Module for testing the add campus command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddCampus(TestBrokerCommand):

    def testaddte(self):
        self.dsdb_expect_add_campus("ta", "Test Comment")
        command = ["add", "campus", "--campus", "ta", "--country", "us",
                   "--comments", "Test Comment", "--fullname", "Test Campus"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddte(self):
        command = "show campus --campus ta"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Campus: ta", command)
        self.matchoutput(out, "Fullname: Test Campus", command)
        self.matchoutput(out, "Comments: Test Comment", command)

    def testverifyaddbuproto(self):
        command = "show campus --campus ta --format proto"
        out = self.commandtest(command.split(" "))
        locs = self.parse_location_msg(out, 1)
        self.matchoutput(locs.locations[0].name, "ta", command)
        self.matchoutput(locs.locations[0].location_type, "campus", command)

    def testverifybuildingall(self):
        command = ["show", "campus", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Campus: ta", command)

    def testverifyshowcsv(self):
        command = "show campus --campus ta --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "campus,ta,country,us", command)

    def testaddln(self):
        self.dsdb_expect_add_campus("ln")
        self.noouttest(["add_campus", "--campus", "ln", "--country", "gb",
                        "--fullname", "London"])
        self.dsdb_verify()

    def testaddny(self):
        self.dsdb_expect_add_campus("ny")
        self.noouttest(["add_campus", "--campus", "ny", "--country", "us",
                        "--fullname", "New York"])
        self.dsdb_verify()

    def testaddvi(self):
        self.dsdb_expect_add_campus("vi")
        self.noouttest(["add_campus", "--campus", "vi", "--country", "us",
                        "--fullname", "Virginia"])
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCampus)
    unittest.TextTestRunner(verbosity=2).run(suite)
