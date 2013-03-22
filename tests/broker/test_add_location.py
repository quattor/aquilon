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
"""Module for testing the add location command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddLocation(TestBrokerCommand):

    def testaddbuagain(self):
        command = ["add", "location", "--type", "building", "--name", "bu",
                   "--parenttype", "city", "--parentname", "ny",
                   "--fullname", "bu"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Building bu already exists.", command)

    def testaddmissingparent(self):
        command = ["add", "location", "--type", "building", "--name", "bt",
                   "--parenttype", "city", "--parentname", "no-such-city",
                   "--fullname", "bt"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "City no-such-city not found.", command)

    def testaddbadtype(self):
        command = ["add", "location", "--type", "bad-type", "--name", "bt",
                   "--parenttype", "city", "--parentname", "ny",
                   "--fullname", "bt"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Bad-type is not a known location type.", command)

    def testaddillegalparent(self):
        command = ["add", "location", "--type", "country", "--name", "bt",
                   "--parenttype", "city", "--parentname", "ny",
                   "--fullname", "bt"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Type City cannot be a parent of Country.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddLocation)
    unittest.TextTestRunner(verbosity=2).run(suite)
