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
"""Module for testing the del bunker command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelBunker(TestBrokerCommand):

    def testdelutbunker1(self):
        command = "del bunker --bunker utbunker1"
        self.noouttest(command.split(" "))

    def testverifydelutbunker1(self):
        command = "show bunker --bunker utbunker1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Bunker utbunker1 not found.", command)

    def testdelbunkernotexist(self):
        command = "del bunker --bunker bunker-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Bunker bunker-does-not-exist not found.", command)

    def testdelbunkernetwork(self):
        test_bunker = "utbunker1"

        # add network to bunker
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--bunker", test_bunker,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete bunker
        command = "del bunker --bunker %s" % test_bunker
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete bunker %s, networks "
                         "were found using this location." % test_bunker,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelBunker)
    unittest.TextTestRunner(verbosity=2).run(suite)
