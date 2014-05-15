#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Module for testing deprecated switch commands."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDeprecatedRouter(TestBrokerCommand):

    def test_100_add_router(self):
        net = self.net["unknown1"]
        command = ["add", "router", "--ip", net.gateway,
                   "--fqdn", "gw-unknown1-vip.aqd-unittest.ms.com",
                   "--building", "ut"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Command add_router is deprecated.", command)

    def test_200_update_router(self):
        command = ["update", "router",
                   "--fqdn", "gw-unknown1-vip.aqd-unittest.ms.com",
                   "--comments", "Test router"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Command update_router is deprecated.", command)

    def test_300_show_router(self):
        net = self.net["unknown1"]
        command = ["show", "router", "--ip", net.gateway]
        (out, err) = self.successtest(command)
        #self.matchoutput(err, "Command show_router is deprecated.", command)
        self.matchoutput(out,
                         "Router: gw-unknown1-vip.aqd-unittest.ms.com [%s]"
                         % net.gateway,
                         command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Comments: Test router", command)

    def test_400_del_router(self):
        command = ["del", "router",
                   "--fqdn", "gw-unknown1-vip.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Command del_router is deprecated.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeprecatedRouter)
    unittest.TextTestRunner(verbosity=2).run(suite)
