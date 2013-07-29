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
"""Module for testing the del campus command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelCampus(TestBrokerCommand):

    def testdelte(self):
        self.dsdb_expect_del_campus("ta")
        command = "del campus --campus ta"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydelte(self):
        command = "show campus --campus ta"
        self.notfoundtest(command.split(" "))

    def testdelbunotindsdb(self):
        ## add campus

        test_campus = "bz"
        self.dsdb_expect_add_campus(test_campus)
        command = ["add", "campus", "--campus", test_campus, "--country", "us"]
        self.successtest(command)
        self.dsdb_verify()

        errstr = "campus %s doesn't exist" % test_campus
        self.dsdb_expect_del_campus(test_campus, fail=True, errstr=errstr)
        command = "del campus --campus %s" % test_campus
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelCampus)
    unittest.TextTestRunner(verbosity=2).run(suite)
