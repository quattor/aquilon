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
"""Module for testing the add organization command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestOrganization(TestBrokerCommand):

    def test_100_add_example(self):
        command = ["add", "organization", "--organization", "example",
                   "--fullname", "Example, Inc"]
        self.noouttest(command)

    def test_100_add_example2(self):
        command = ["add", "organization", "--organization", "example2"]
        self.noouttest(command)

    def test_110_show_example(self):
        command = "show organization --organization example"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Organization: example", command)

    def test_110_show_example2(self):
        command = "show organization --organization example2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Organization: example2", command)

    def test_120_add_ms(self):
        command = ["add_organization", "--organization", "ms",
                   "--fullname", "Morgan Stanley"]
        self.noouttest(command)

    def test_200_add_example_net(self):
        self.net.allocate_network(self, "example_org_net", 24, "unknown",
                                  "organization", "example",
                                  comments="Made-up network")

    def test_201_del_example_fail(self):
        command = "del organization --organization example"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete organization example, "
                         "networks were found using this location.",
                         command)

    def test_202_cleanup_example_net(self):
        self.net.dispose_network(self, "example_org_net")

    def test_210_del_example(self):
        command = "del organization --organization example"
        self.noouttest(command.split(" "))

    def test_220_del_example2(self):
        command = "del organization --organization example2"
        self.noouttest(command.split(" "))

    def test_220_del_example2_again(self):
        command = "del organization --organization example2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization example2 not found.", command)

    def test_230_del_notexist(self):
        command = "del organization --organization org-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization org-does-not-exist not found.",
                         command)

    def test_300_verify_example2(self):
        command = "show organization --organization example2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization example2 not found.", command)

    def test_300_show_all(self):
        command = ["show_organization", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "ms", command)
        self.matchclean(out, "example", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrganization)
    unittest.TextTestRunner(verbosity=2).run(suite)
