#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015  Contributor
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
"""Module for testing the update network command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestUpdateNetwork(TestBrokerCommand):

    def test_100_update(self):
        command = ["update", "network", "--network", "excx-net",
                   "--network_environment", "excx",
                   "--building", "ut", "--type", "dmz-net",
                   "--side", "b", "--comments", "New network comments"]
        self.noouttest(command)

    def test_110_verify(self):
        command = ["show", "network", "--network", "excx-net",
                   "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchoutput(out, "Comments: New network comments", command)
        self.matchoutput(out, "Sysloc: ut.ny.na", command)
        self.matchoutput(out, "Network Type: dmz-net", command)
        self.matchoutput(out, "Side: b", command)

    def test_200_update_utdmz1(self):
        net = self.net["ut_dmz1"]
        command = ["update_network",
                   "--ip=%s" % net.ip,
                   "--network_compartment="]
        self.noouttest(command)

    def test_201_verify_utdmz1(self):
        command = ["search", "network", "--network_compartment", "perimeter.ut"]
        self.noouttest(command)

    # There should be a test_constraint_network.py one day...
    def test_900_delinuse(self):
        net = self.net["unknown0"]
        command = ["del", "network", "--ip", net.ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Network %s [%s] is still in use" %
                         (net.name, net), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
