#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the add city command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddCity(TestBrokerCommand):

    def test_100_add_example(self):
        self.dsdb_expect("add_city_aq -city_symbol ex " +
                         "-country_symbol us -city_name Exampleton")
        command = ["add", "city", "--city", "ex", "--country", "us",
                   "--fullname", "Exampleton", "--timezone",
                   "US/Eastern", "--comments", "Example city comment"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_verify_example(self):
        command = ["show_city", "--city", "ex"]
        out = self.commandtest(command)
        self.matchoutput(out, "City: ex", command)
        self.matchoutput(out,
                         "Location Parents: [Organization ms, Hub ny, Continent na, Country us]",
                         command)
        self.matchoutput(out, "Fullname: Exampleton", command)
        self.matchoutput(out, "Timezone: US/Eastern", command)
        self.matchoutput(out, "Comments: Example city comment", command)

    def test_110_update_example(self):
        command = ["update", "city", "--city", "ex",
                   "--timezone", "EDT", "--fullname", "New Exampleton",
                   "--comments", "Exampleton city comment"]
        out = self.statustest(command)
        self.matchoutput(out, "Flushed 1 templates.", command)

    def test_115_verify_update(self):
        command = "show city --city ex"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Fullname: New Exampleton", command)
        self.matchoutput(out, "Timezone: EDT", command)
        self.matchoutput(out, "Comments: Exampleton city comment", command)

    def test_115_verify_exampe_proto(self):
        command = "show city --city ex --format proto"
        out = self.commandtest(command.split(" "))
        locs = self.parse_location_msg(out, 1)
        self.matchoutput(locs.locations[0].name, "ex", command)
        self.matchoutput(locs.locations[0].location_type, "city", command)
        self.matchoutput(locs.locations[0].fullname, "New Exampleton", command)
        self.matchoutput(locs.locations[0].timezone, "EDT", command)

    def test_115_verify_example_plenary(self):
        command = ["cat", "--city", "ex"]
        out = self.commandtest(command)
        self.matchoutput(out, 'variable TIMEZONE = "EDT";', command)

    def test_115_verify_example_csv(self):
        command = "show city --city ex --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "city,ex,country,us,,,EDT,New Exampleton",
                         command)

    def test_120_add_default_tz(self):
        self.dsdb_expect("add_city_aq -city_symbol e3 " +
                         "-country_symbol us -city_name Exampleby")
        command = ["add", "city", "--city", "e3", "--country", "us",
                   "--fullname", "Exampleby", "--timezone", "UTC"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_125_verify_default_tz_cat(self):
        command = ["cat", "--city", "e3"]
        out = self.commandtest(command)
        self.matchoutput(out, 'variable TIMEZONE = "UTC";', command)

    def test_130_add_ln(self):
        self.dsdb_expect("add_city_aq -city_symbol ln " +
                         "-country_symbol gb -city_name London")
        self.noouttest(["add_city", "--city", "ln", "--campus", "ln",
                        "--fullname", "London", "--timezone", "Europe/London"])
        self.dsdb_verify()

    def test_140_add_ny(self):
        self.dsdb_expect("add_city_aq -city_symbol ny " +
                         "-country_symbol us -city_name New York")
        self.noouttest(["add_city", "--city", "ny", "--campus", "ny",
                        "--fullname", "New York", "--timezone", "US/Eastern"])
        self.dsdb_verify()

    def test_141_update_default_dns(self):
        command = ["update", "city", "--city", "ny",
                   "--default_dns_domain", "one-nyp.ms.com"]
        self.successtest(command)

    def test_145_verify_default_dns(self):
        command = ["show", "city", "--city", "ny"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: one-nyp.ms.com", command)

    def test_150_add_e5(self):
        self.dsdb_expect("add_city_aq -city_symbol e5 " +
                         "-country_symbol us -city_name Examplefive")
        command = ["add", "city", "--city", "e5", "--campus", "ta",
                   "--fullname", "Examplefive", "--timezone", "US/Eastern"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_200_add_example_fail(self):
        self.dsdb_expect("add_city_aq -city_symbol e2 " +
                         "-country_symbol us -city_name Exampleville",
                         fail=True)
        command = ["add", "city", "--city", "e2", "--country", "us",
                   "--fullname", "Exampleville", "--timezone",
                   "US/Eastern"]
        self.badrequesttest(command)
        self.dsdb_verify()

    def test_300_show_city_all(self):
        command = ["show", "city", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "City: ex", command)
        self.matchoutput(out, "City: e3", command)
        self.matchclean(out, "e2", command)

    def test_400_update_city_campus(self):
        ## add city
        self.dsdb_expect("add_city_aq -city_symbol e4 " +
                         "-country_symbol us -city_name Exampleby")
        command = ["add", "city", "--city", "e4", "--country", "us",
                   "--fullname", "Exampleby", "--timezone", "US/Eastern"]
        self.noouttest(command)
        self.dsdb_verify()

        ## add building
        self.dsdb_expect("add_building_aq -building_name bx -city e4 "
                         "-building_addr Nowhere")
        command = ["add", "building", "--building", "bx", "--city", "e4",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

        ## add campus
        self.dsdb_expect_add_campus("na")
        command = ["add", "campus", "--campus", "na", "--country", "us",
                   "--fullname", "test campus"]
        self.noouttest(command)
        self.dsdb_verify()

        # update city
        self.dsdb_expect("update_city_aq -city e4 -campus na")
        command = ["update", "city", "--city", "e4", "--campus", "na"]
        self.ignoreoutputtest(command)
        self.dsdb_verify()

        command = "show city --city e4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na]", command)

        command = "show building --building bx"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na, City e4]",
                         command)

    def test_410_update_city_no_campus(self):
        command = ["update", "city", "--city", "e4", "--campus", "xx"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Campus xx not found", command)

        command = "show city --city e4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na]", command)

    def test_420_update_city_dsdb_error(self):
        self.dsdb_expect("update_city_aq -city e4 -campus ta", fail=True)
        command = ["update", "city", "--city", "e4", "--campus", "ta"]
        out = self.badrequesttest(command)
        self.dsdb_verify()

        command = "show city --city e4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na]", command)

    def test_430_update_city_30_bad_campus(self):
        ## add city
        self.dsdb_expect("add_city_aq -city_symbol e6 " +
                         "-country_symbol gb -city_name ExampleSix")

        command = ["add", "city", "--city", "e6", "--country", "gb",
                   "--fullname", "ExampleSix", "--timezone", "Europe/London"]
        self.noouttest(command)
        self.dsdb_verify()

        ## update city bad campus
        command = ["update", "city", "--city", "e6", "--campus", "na"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cannot change campus.  Campus na is in hub ny, while city e6 is in hub ln", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCity)
    unittest.TextTestRunner(verbosity=2).run(suite)
