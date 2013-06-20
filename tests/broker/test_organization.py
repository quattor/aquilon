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
"""Module for testing the add organization command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestOrganization(TestBrokerCommand):

    def test_100_addexorg(self):
        command = ["add", "organization", "--organization", "example",
                   "--fullname", "Example, Inc"]
        self.noouttest(command)

        command = "show organization --organization example"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Organization: example", command)

    def test_100_addexorg2(self):
        command = ["add", "organization", "--organization", "example2"]
        self.noouttest(command)

        command = "show organization --organization example2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Organization: example2", command)

    def test_110_delexorg2(self):
        command = "del organization --organization example2"
        self.noouttest(command.split(" "))

    def test_120_delexorg2again(self):
        command = "del organization --organization example2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization example2 not found.", command)

    def test_130_verifydelexorg2(self):
        command = "show organization --organization example2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization example2 not found.", command)

    def test_140_delexorginuse(self):
        test_org = "example"

        # add network to org
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--organization", test_org,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete org
        command = "del organization --organization %s" % test_org
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete organization %s, "
                         "networks were found using this location." % test_org,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def test_150_delexorg1(self):
        command = "del organization --organization example"
        self.noouttest(command.split(" "))

    def test_160_add_ms(self):
        command = ["add_organization", "--organization", "ms",
                   "--fullname", "Morgan Stanley"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrganization)
    unittest.TextTestRunner(verbosity=2).run(suite)
