#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016,2017  Contributor
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
"""Module for testing the add_network_compartment command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddNetworkCompartment(TestBrokerCommand):

    def test_100_bad_name(self):
        command = ["add", "network", "compartment",
                   "--network_compartment", "<badname>"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "llegal network compartment tag '<badname>'",
                         command)

    def test_101_add_utper(self):
        command = ["add", "network", "compartment",
                   "--network_compartment", "perimeter.ut",
                   "--comments", "Unit-test Permiter DMZ", "--justification", "tcm=123"]
        self.noouttest(command)

    def test_102_add_utint(self):
        command = ["add", "network", "compartment",
                   "--network_compartment", "interior.ut",
                   "--comments", "Unit-test Interior", "--justification", "tcm=123"]
        self.noouttest(command)

    def test_109_add_utint_again(self):
        command = ["add", "network", "compartment",
                   "--network_compartment", "interior.ut"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network Compartment interior.ut already exists",
                         command)

    def test_201_show_utper(self):
        command = ["show", "network", "compartment",
                   "--network_compartment", "perimeter.ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Compartment: perimeter.ut",
                         command)
        self.matchoutput(out, "Comments: Unit-test Permiter DMZ", command)

    def test_202_show_utper_proto(self):
        command = ["show", "network", "compartment",
                   "--network_compartment", "perimeter.ut", "--format", "proto"]
        compartment = self.protobuftest(command, expect=1)[0]
        self.assertEqual(compartment.name, "perimeter.ut")

    def test_209_show_nonexistant(self):
        command = ["show", "network", "compartment",
                   "--network_compartment", "nonexistant"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Network Compartment nonexistant not found",
                         command)

    def test_500_show_all(self):
        command = ["show", "network", "compartment", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Compartment: perimeter.ut",
                         command)
        self.matchoutput(out, "Network Compartment: interior.ut", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetworkCompartment)
    unittest.TextTestRunner(verbosity=2).run(suite)
