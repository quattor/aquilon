#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del_router command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelRouter(TestBrokerCommand):

    def testdelrouterbyip(self):
        net = self.net.tor_net[6]
        command = ["del", "router", "--ip", net.gateway]
        self.noouttest(command)

    def testdelrouterbyname(self):
        command = ["del", "router",
                   "--fqdn", "ut3gd1r01-v109-hsrp.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testdelmissingrouter(self):
        net = self.net.unknown[0]
        command = ["del", "router", "--ip", net.gateway]
        out = self.notfoundtest(command)
        self.matchoutput(out, "IP address %s is not a router on network %s." %
                         (net.gateway, net.ip), command)

    def testverifyrouter(self):
        command = ["show", "router", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, str(self.net.tor_net[12].gateway), command)
        self.matchclean(out, str(self.net.tor_net[6].gateway), command)

    def testdelexcx(self):
        net = self.net.unknown[0].subnet()[0]
        command = ["del", "router", "--ip", net[-2],
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testdelutcolo(self):
        net = self.net.unknown[1]
        command = ["del", "router", "--ip", net[2],
                   "--network_environment", "utcolo"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRouter)
    unittest.TextTestRunner(verbosity=2).run(suite)
