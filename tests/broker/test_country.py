#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestCountry(TestBrokerCommand):

    def testadd(self):
        command = ["add", "country", "--country", "ct", "--fullname",
                   "country example", "--continent", "na",
                   "--comments", "test country"]
        self.noouttest(command)

    def testaddshow(self):
        command = "show country --country ct"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Country: ct", command)
        self.matchoutput(out, "  Fullname: country example", command)
        self.matchoutput(out, "  Comments: test country", command)
        self.matchoutput(out,
                         "  Location Parents: [Organization ms, Hub ny, "
                         "Continent na]",
                         command)

        command = "show country --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Country: ct", command)

    def testverifydel(self):
        command = "show country --country ct"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Country ct not found.", command)

        command = "show country --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Country: ct", command)

    def testdel(self):
        test_country = "ct"

        # add network to hub
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--country", test_country,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete country
        command = "del country --country %s" % test_country
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete country %s, networks "
                         "were found using this location." % test_country,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def testdel01(self):
        command = "del country --country ct"
        self.noouttest(command.split(" "))

        ## delete country again
        command = "del country --country ct"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Country ct not found.", command)

    def testaddgb(self):
        self.noouttest(["add_country", "--country", "gb", "--continent", "eu",
                        "--fullname", "Great Britain"])

    def testaddus(self):
        self.noouttest(["add_country", "--country", "us", "--continent", "na",
                        "--fullname", "USA"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCountry)
    unittest.TextTestRunner(verbosity=2).run(suite)
