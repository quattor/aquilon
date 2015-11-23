#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Module for testing the del_network_compartment command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestDelNetworkCompartment(TestBrokerCommand):

    def test_100_del_utint(self):
        command = ["del", "network", "compartment",
                   "--network_compartment", "interior.ut"]
        self.noouttest(command)

    def test_105_verify_utint(self):
        command = ["show", "network", "compartment",
                   "--network_compartment", "interior.ut"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Network Compartment interior.ut not found.", command)

    def test_110_del_utper(self):
        command = ["del", "network", "compartment",
                   "--network_compartment", "perimeter.ut"]
        self.noouttest(command)

    def test_300_verify_all(self):
        command = ["show", "network", "compartment", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "perimeter.ut", command)
        self.matchclean(out, "interior.ut", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNetworkCompartment)
    unittest.TextTestRunner(verbosity=2).run(suite)
