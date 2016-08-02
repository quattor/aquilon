#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the del_router_address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelRouterAddress(TestBrokerCommand):

    def test_100_del_router_by_ip(self):
        net = self.net["verari_eth1"]
        command = ["del", "router", "address", "--ip", net.gateway]
        self.noouttest(command)

    def test_110_del_router_by_name(self):
        command = ["del", "router", "address",
                   "--fqdn", "ut3gd1r01-v109-hsrp.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_120_del_excx(self):
        net = self.net["unknown0"].subnet()[0]
        command = ["del", "router", "address", "--ip", net[-2],
                   "--network_environment", "excx"]
        self.noouttest(command)

    def test_130_del_utcolo(self):
        net = self.net["unknown1"]
        command = ["del", "router", "address", "--ip", net[2],
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def test_200_del_missing_router(self):
        net = self.net["unknown0"]
        command = ["del", "router", "address", "--ip", net.gateway]
        out = self.notfoundtest(command)
        self.matchoutput(out, "IP address %s is not a router on network %s [%s]."
                         % (net.gateway, net.name, net), command)

    def test_300_verify_all(self):
        command = ["show", "router", "address", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, str(self.net["tor_net_12"].gateway), command)
        self.matchclean(out, str(self.net["verari_eth1"].gateway), command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRouterAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
