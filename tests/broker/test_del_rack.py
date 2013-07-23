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
"""Module for testing the del rack command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelRack(TestBrokerCommand):

    def test_100_del_ut3(self):
        command = "del rack --rack ut3"
        self.noouttest(command.split(" "))

    def test_100_del_np3(self):
        command = "del rack --rack np3"
        self.noouttest(command.split(" "))

    def test_100_del_ut4(self):
        command = "del rack --rack ut4"
        self.noouttest(command.split(" "))

    def test_100_del_np997(self):
        command = "del rack --rack np997"
        self.noouttest(command.split(" "))

    def test_100_del_np998(self):
        command = "del rack --rack np998"
        self.noouttest(command.split(" "))

    def test_100_del_np999(self):
        command = "del rack --rack np999"
        self.noouttest(command.split(" "))

    def test_100_del_ut8(self):
        command = "del rack --rack ut8"
        self.noouttest(command.split(" "))

    def test_100_del_cards(self):
        command = "del rack --rack cards1"
        self.noouttest(command.split(" "))

    def test_110_add_ut9_net(self):
        self.net.allocate_network(self, "ut9_net", 24, "unknown", "rack", "ut9",
                                  comments="Made-up network")

    def test_111_del_ut9_fail(self):
        command = "del rack --rack ut9"
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete rack ut9, networks "
                         "were found using this location.",
                         command)

    def test_112_cleanup_ut9_net(self):
        self.net.dispose_network(self, "ut9_net")

    def test_120_del_ut9(self):
        command = "del rack --rack ut9"
        self.noouttest(command.split(" "))

    def test_200_del_ut9_again(self):
        command = ["del_rack", "--rack", "ut9"]
        self.notfoundtest(command)

    def test_200_del_notexist(self):
        command = ["del_rack", "--rack", "rack-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Rack rack-does-not-exist not found.", command)

    def test_300_verify_ut3(self):
        command = "show rack --rack ut3"
        self.notfoundtest(command.split(" "))

    def test_300_verify_ut9(self):
        command = "show rack --rack ut9"
        self.notfoundtest(command.split(" "))

    def test_300_verify_cards(self):
        command = "show rack --rack cards1"
        self.notfoundtest(command.split(" "))

    def test_300_show_all(self):
        command = ["show_rack", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "ut3", command)
        self.matchclean(out, "ut4", command)
        self.matchclean(out, "ut8", command)
        self.matchclean(out, "ut9", command)
        self.matchclean(out, "np3", command)
        self.matchclean(out, "np997", command)
        self.matchclean(out, "np998", command)
        self.matchclean(out, "np999", command)
        self.matchclean(out, "cards1", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRack)
    unittest.TextTestRunner(verbosity=2).run(suite)
