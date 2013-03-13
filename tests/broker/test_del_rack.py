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
"""Module for testing the del rack command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelRack(TestBrokerCommand):

    def testdelut3(self):
        command = "del rack --rack ut3"
        self.noouttest(command.split(" "))

    def testverifydelut3(self):
        command = "show rack --rack ut3"
        self.notfoundtest(command.split(" "))

    def testdelnp3(self):
        command = "del rack --rack np3"
        self.noouttest(command.split(" "))

    def testdelut4(self):
        command = "del rack --rack ut4"
        self.noouttest(command.split(" "))

    def testdelnp997(self):
        command = "del rack --rack np997"
        self.noouttest(command.split(" "))

    def testverifydelnp997(self):
        command = "show rack --rack np997"
        self.notfoundtest(command.split(" "))

    def testdelnp998(self):
        command = "del rack --rack np998"
        self.noouttest(command.split(" "))

    def testverifydelnp998(self):
        command = "show rack --rack np998"
        self.notfoundtest(command.split(" "))

    def testdelnp999(self):
        command = "del rack --rack np999"
        self.noouttest(command.split(" "))

    def testverifydelnp999(self):
        command = "show rack --rack np999"
        self.notfoundtest(command.split(" "))

    # FIXME: Maybe del_switch should remove the rack if it is
    # otherwise empty.
    def testdelut8(self):
        command = "del rack --rack ut8"
        self.noouttest(command.split(" "))

    def testverifydelut8(self):
        command = "show rack --rack ut8"
        self.notfoundtest(command.split(" "))

    def testdelut9(self):
        command = "del rack --rack ut9"
        self.noouttest(command.split(" "))

    def testverifydelut9(self):
        command = "show rack --rack ut9"
        self.notfoundtest(command.split(" "))

    def testdelcards(self):
        command = "del rack --rack cards1"
        self.noouttest(command.split(" "))

    def testverifyvards(self):
        command = "show rack --rack cards1"
        self.notfoundtest(command.split(" "))

    def testdelracknetwork(self):
        test_rack = "ut9"

        # add network to rack
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--rack", test_rack,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete rack
        command = "del rack --rack %s" % test_rack
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete rack %s, networks "
                         "were found using this location." % test_rack,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRack)
    unittest.TextTestRunner(verbosity=2).run(suite)
