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
"""Module for testing the behavior of network compartment."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUpdateNetworkCompartment(TestBrokerCommand):

    def test_100_update_comments(self):
        command = ["update", "network", "compartment",
                   "--network_compartment", "interior.ut",
                   "--comments", "Unit-test Interior Networks"]
        self.noouttest(command)

    def test_105_verify_comments(self):
        command = ["show", "network", "compartment",
                   "--network_compartment", "interior.ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Compartment: interior.ut",
                         command)
        self.matchoutput(out, "Comments: Unit-test Interior Networks",
                         command)

    def test_200_update_nonexistant(self):
        command = ["update", "network", "compartment",
                   "--network_compartment", "nonexistant",
                   "--comments", "Should never work"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Network Compartment nonexistant not found",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateNetworkCompartment)
    unittest.TextTestRunner(verbosity=2).run(suite)
