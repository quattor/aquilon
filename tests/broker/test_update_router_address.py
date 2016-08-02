#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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
"""Module for testing the update_router_address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateRouterAddress(TestBrokerCommand):

    def test_100_update_router(self):
        net = self.net["verari_eth1"]
        command = ["update_router_address", "--ip", net.gateway,
                   "--building", "np",
                   "--comments", "New router address comments"]
        self.noouttest(command)

    def test_105_show_router(self):
        net = self.net["verari_eth1"]
        command = ["show", "router", "address", "--ip", net.gateway]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Router: ut3gd1r04-v109-hsrp.aqd-unittest.ms.com [%s]"
                         % net.gateway,
                         command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Comments: New router address comments", command)
        self.matchoutput(out, "Building: np", command)

    def test_110_clear_location_comments(self):
        net = self.net["verari_eth1"]
        command = ["update_router_address", "--ip", net.gateway,
                   "--clear_location", "--comments", ""]
        self.noouttest(command)

    def test_115_verify_clear(self):
        net = self.net["verari_eth1"]
        command = ["show", "router", "address", "--ip", net.gateway]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Router: ut3gd1r04-v109-hsrp.aqd-unittest.ms.com [%s]"
                         % net.gateway,
                         command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchclean(out, "Building", command)
        self.matchclean(out, "Comments", command)

    def test_120_update_excx(self):
        net = self.net["unknown0"].subnet()[0]
        command = ["update_router_address", "--ip", net[-2],
                   "--network_environment", "excx",
                   "--comments", "New other router address comments"]
        self.noouttest(command)

    def test_125_show_excx(self):
        command = ["show", "router", "address", "--network_environment", "excx", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Router: gw1.excx.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Comments: New other router address comments",
                         command)

    def test_200_update_wrong_env(self):
        # This address exists as a router in excx, but not in utcolo
        net = self.net["unknown0"].subnet()[0]
        command = ["update_router_address", "--ip", net[-2],
                   "--network_environment", "utcolo",
                   "--comments", "New other router address comments"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Could not determine network containing IP address %s." % net[-2],
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateRouterAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
