#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the add/del/show hub command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestHub(TestBrokerCommand):

    def test_100_add_hub1_default_org(self):
        command = ["add", "hub", "--hub", "hub1", "--fullname",
                   "hub1 example", "--comments", "test hub1"]
        self.noouttest(command)

    def test_110_add_hubtest_org(self):
        command = ["add", "organization", "--organization", "hubtest",
                   "--fullname", "Hub Test, Inc"]
        self.noouttest(command)

    def test_115_add_hub2(self):
        command = ["add", "hub", "--hub", "hub2", "--fullname", "hub2 example",
                   "--organization", "hubtest", "--comments", "test hub2"]
        self.noouttest(command)

    def test_120_add_hk(self):
        self.noouttest(["add_hub", "--hub", "hk", "--organization", "ms",
                        "--fullname", "Non-Japan-Asia"])

    def test_120_add_ln(self):
        self.noouttest(["add_hub", "--hub", "ln", "--organization", "ms",
                        "--fullname", "Europa"])

    def test_120_add_ny(self):
        self.noouttest(["add_hub", "--hub", "ny", "--organization", "ms",
                        "--fullname", "Americas"])

    def test_130_verify_hub1(self):
        command = "show hub --hub hub1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub1", command)
        self.matchoutput(out, "  Fullname: hub1 example", command)
        self.matchoutput(out, "  Comments: test hub1", command)
        self.matchoutput(out, "  Location Parents: [Organization ms]", command)

    def test_130_verify_hub2(self):
        command = "show hub --hub hub2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub2", command)
        self.matchoutput(out, "  Fullname: hub2 example", command)
        self.matchoutput(out, "  Comments: test hub2", command)
        self.matchoutput(out, "  Location Parents: [Organization hubtest]",
                         command)

    def test_130_show_all(self):
        command = "show hub --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub1", command)
        self.matchoutput(out, "Hub: hub2", command)

    def test_200_add_hub1_net(self):
        self.net.allocate_network(self, "hub1_net", 24, "unknown", "hub", "hub1",
                                  comments="Made-up network")

    def test_201_del_hub1_fail(self):
        command = "del hub --hub hub1"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete hub hub1, networks "
                         "were found using this location.",
                         command)

    def test_202_cleanup_hub1_net(self):
        self.net.dispose_network(self, "hub1_net")

    def test_210_del_hub1(self):
        command = "del hub --hub hub1"
        self.noouttest(command.split(" "))

    def test_220_del_hub1_again(self):
        command = "del hub --hub hub1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub1 not found.", command)

    def test_230_del_hub2(self):
        command = "del hub --hub hub2"
        self.noouttest(command.split(" "))

    def test_240_del_hubtest_org(self):
        command = "del organization --organization hubtest"
        self.noouttest(command.split(" "))

    def test_300_verify_hub1(self):
        command = "show hub --hub hub1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub1 not found.", command)

    def test_300_verify_hub2(self):
        command = "show hub --hub hub2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub2 not found.", command)

    def test_300_verify_all(self):
        command = "show hub --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Hub: hub1", command)
        self.matchclean(out, "Hub: hub2", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
