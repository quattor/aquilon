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
"""Module for testing the del city command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelCity(TestBrokerCommand):
    """ test delete city functionality """

    def test_100_add_ex_net(self):
        self.net.allocate_network(self, "ex_net", 24, "unknown",
                                  "city", "ex",
                                  comments="Made-up network")

    def test_101_del_ex_fail(self):
        command = "del_city --city ex"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete city ex, networks "
                         "were found using this location.",
                         command)

    def test_102_cleanup_ex_net(self):
        self.net.dispose_network(self, "ex_net")

    def test_110_del_ex(self):
        command = ["del_city", "--city=ex"]
        self.dsdb_expect("delete_city_aq -city ex")
        self.successtest(command)
        self.dsdb_verify()
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "site", "americas", "ex")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)

    def test_200_del_notexist(self):
        command = ["del_city", "--city", "city-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "City city-does-not-exist not found.", command)

    def test_300_verify_ex(self):
        command = ["show_city", "--city", "ex"]
        self.notfoundtest(command)

    def test_300_verify_all(self):
        command = ["show_city", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "ex", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelCity)
    unittest.TextTestRunner(verbosity=2).run(suite)
