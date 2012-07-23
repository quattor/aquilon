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
"""Module for testing the add/del/show hub command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestHub(TestBrokerCommand):

    def testaddhub(self):
        command = ["add", "hub", "--hub", "hub1", "--fullname",
                   "hub1 example", "--comments", "test hub1"]
        self.noouttest(command)

        command = ["add", "organization", "--organization", "example",
                   "--fullname", "Example, Inc"]
        self.noouttest(command)

        command = ["add", "hub", "--hub", "hub2", "--fullname", "hub2 example",
                   "--organization", "example", "--comments", "test hub2"]
        self.noouttest(command)

    def testaddhubshow(self):
        command = "show hub --hub hub1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub1", command)
        self.matchoutput(out, "  Fullname: hub1 example", command)
        self.matchoutput(out, "  Comments: test hub1", command)
        self.matchoutput(out, "  Location Parents: [Organization ms]", command)

        command = "show hub --hub hub2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub2", command)
        self.matchoutput(out, "  Fullname: hub2 example", command)
        self.matchoutput(out, "  Comments: test hub2", command)
        self.matchoutput(out, "  Location Parents: [Organization example]",
                         command)

        command = "show hub --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub1", command)
        self.matchoutput(out, "Hub: hub2", command)

    def testverifydelhub(self):
        command = "show hub --hub hub1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub1 not found.", command)

        command = "show hub --hub hub2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub2 not found.", command)

        command = "show hub --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Hub: hub1", command)
        self.matchclean(out, "Hub: hub2", command)

    def testdelhub(self):
        test_hub = "hub1"

        # add network to hub
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--hub", test_hub,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete hub
        command = "del hub --hub %s" % test_hub
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete hub %s, networks "
                         "were found using this location." % test_hub,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def testdelhub01(self):
        command = "del hub --hub hub1"
        self.noouttest(command.split(" "))

        ## delete hub1 again
        command = "del hub --hub hub1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub1 not found.", command)

    def testdelhub02(self):
        command = "del hub --hub hub2"
        self.noouttest(command.split(" "))

        ## delete hub2 again
        command = "del hub --hub hub2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub2 not found.", command)

        command = "del organization --organization example"
        self.noouttest(command.split(" "))

    def testaddhk(self):
        self.noouttest(["add_hub", "--hub", "hk", "--organization", "ms",
                        "--fullname", "Non-Japan-Asia"])

    def testaddln(self):
        self.noouttest(["add_hub", "--hub", "ln", "--organization", "ms",
                        "--fullname", "Europa"])

    def testaddny(self):
        self.noouttest(["add_hub", "--hub", "ny", "--organization", "ms",
                        "--fullname", "Americas"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
