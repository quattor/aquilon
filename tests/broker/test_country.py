#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011-2013,2015-2016,2019  Contributor
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
"""Module for testing the add/del/show country command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from utils import MockHub


class TestCountry(TestBrokerCommand):

    def test_100_add(self):
        command = ["add", "country", "--country", "ct", "--fullname",
                   "country example", "--continent", "na",
                   "--comments", "Some country comments"]
        self.noouttest(command)

    def test_110_show_ct(self):
        command = "show country --country ct"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Country: ct", command)
        self.matchoutput(out, "  Fullname: country example", command)
        self.matchoutput(out, "  Comments: Some country comments", command)
        self.matchoutput(out,
                         "  Location Parents: [Organization ms, Hub ny, "
                         "Continent na]",
                         command)

    def test_110_show_all(self):
        command = "show country --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Country: ct", command)

    def test_120_add_gb(self):
        self.noouttest(["add_country", "--country", "gb", "--continent", "eu",
                        "--fullname", "Great Britain"])

    def test_120_add_us(self):
        self.noouttest(["add_country", "--country", "us", "--continent", "na",
                        "--fullname", "USA"])

    def test_200_add_ct_net(self):
        self.net.allocate_network(self, "ct_net", 24, "unknown",
                                  "country", "ct",
                                  comments="Made-up network")

    def test_201_del_ct_fail(self):
        command = "del country --country ct"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete country ct, networks "
                         "were found using this location.",
                         command)

    def test_202_cleanup_ct_net(self):
        self.net.dispose_network(self, "ct_net")

    def test_210_del_ct(self):
        command = "del country --country ct"
        self.noouttest(command.split(" "))

    def test_220_del_ct_again(self):
        command = "del country --country ct"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Country ct not found.", command)

    def test_300_verify_del(self):
        command = "show country --country ct"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Country ct not found.", command)

        command = "show country --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Country: ct", command)

    def test_400_del_country_fails_with_warning_if_cities_found(self):
        mh = MockHub(engine=self)
        country = mh.add_country()
        mh.add_city(country=country)

        command = ['del_country', '--country', country]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         'Bad Request: Could not delete country {}, at least '
                         'one city found in this country.'.format(country),
                         command)
        mh.delete()

    def test_400_del_country_can_be_forced_if_cities_found(self):
        # Set up.
        mh = MockHub(engine=self)
        country = mh.add_country()
        mh.add_city(country=country)
        # Test.
        command = ['del_country', '--country', country, '--force_non_empty']
        self.noouttest(command)
        # Confirm the deletion of the country.
        command = ['show_country', '--country', country]
        self.notfoundtest(command)
        # Clean up.
        mh.countries.remove(country)
        mh.delete()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCountry)
    unittest.TextTestRunner(verbosity=2).run(suite)
