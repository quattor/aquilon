#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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

    def test_100_add_ta(self):
        self.dsdb_expect_add_campus("ta", "Some campus comments")
        command = ["add", "campus", "--campus", "ta", "--country", "us",
                   "--fullname", "Test Campus",
                   "--comments", "Some campus comments"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_show_ta(self):
        command = "show campus --campus ta"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Campus: ta", command)
        self.matchoutput(out, "Fullname: Test Campus", command)
        self.matchoutput(out, "Comments: Some campus comments", command)

    def test_105_show_ta_proto(self):
        command = "show campus --campus ta --format proto"
        loc = self.protobuftest(command.split(" "), expect=1)[0]
        self.matchoutput(loc.name, "ta", command)
        self.matchoutput(loc.location_type, "campus", command)

    def test_105_show_ta_csv(self):
        command = "show campus --campus ta --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "campus,ta,country,us", command)

    def test_110_add_ln(self):
        self.dsdb_expect_add_campus("ln")
        self.noouttest(["add_campus", "--campus", "ln", "--country", "gb",
                        "--fullname", "London"])
        self.dsdb_verify()

    def test_115_add_ny(self):
        self.dsdb_expect_add_campus("ny")
        self.noouttest(["add_campus", "--campus", "ny", "--country", "us",
                        "--fullname", "New York"])
        self.dsdb_verify()

    def test_120_add_vi(self):
        self.dsdb_expect_add_campus("vi")
        self.noouttest(["add_campus", "--campus", "vi", "--country", "us",
                        "--fullname", "Virginia"])
        self.dsdb_verify()

    def test_300_show_all(self):
        command = ["show", "campus", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Campus: ta", command)

    def test_200_add_ta_again(self):
        command = ["add", "campus", "--campus", "ta", "--country", "us",
                   "--fullname", "Test Campus"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Campus ta already exists.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCampus)
    unittest.TextTestRunner(verbosity=2).run(suite)
