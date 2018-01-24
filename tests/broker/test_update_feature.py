#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2018  Contributor
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
"""Module for testing the update feature command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestUpdateFeature(TestBrokerCommand):

    @classmethod
    def setUpClass(cls):
        super(TestUpdateFeature, cls).setUpClass()
        cls.proto = cls.protocols['aqdsystems_pb2']

    def test_100_update_feature(self):
        command = ["update", "feature", "--feature", "pre_host", "--eon_id", 3,
                   "--type", "host", "--comments", "New feature comments",
                   "--visibility", "restricted", "--activation", "dispatch", "--deactivation", "rebuild"]
        self.noouttest(command)

    def test_105_verify_show(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.searchoutput(out, r"Host Feature: pre_host\s*"
                               r"Post Personality: False\s*"
                               r"Owned by GRN: grn:/ms/ei/aquilon/unittest\s*"
                               r"Visibility: restricted\s*"
                               r"Activation: dispatch\s*"
                               r"Deactivation: rebuild\s*"
                               r"Template: features/pre_host\s*",
                          command)
        self.matchoutput(out,
                         "Bound to: Personality aquilon/inventory",
                         command)
        self.matchoutput(out,
                         "Bound to: Archetype aquilon",
                         command)
        self.matchoutput(out,
                         "Comments: New feature comments",
                         command)

    def test_105_verify_show_proto(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host", "--format", "proto"]
        feature = self.protobuftest(command, expect=1)[0]
        self.assertEqual(feature.name, "pre_host")
        self.assertEqual(feature.type, "host")
        self.assertEqual(feature.owner_eonid, 3)
        self.assertEqual(feature.visibility, feature.RESTRICTED)
        self.assertEqual(feature.activation, self.proto.DISPATCH)
        self.assertEqual(feature.deactivation, self.proto.REBUILD)
        self.assertEqual(feature.comments, "New feature comments")

    def test_110_update_feature_legacy(self):
        command = ["update", "feature", "--feature", "pre_host", "--type", "host",
                   "--visibility", "legacy"]
        self.noouttest(command)

    def test_115_verify_show(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Visibility: legacy", command)

    def test_200_bad_activation(self):
        command = ["update", "feature", "--feature", "pre_host", "--eon_id", 3,
                   "--type", "host", "--comments", "New feature comments",
                   "--visibility", "restricted", "--activation", "bad_activation"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown value for activation. Valid values are: "
                         "dispatch, reboot, rebuild.",
                         command)

    def test_200_bad_deactivation(self):
        command = ["update", "feature", "--feature", "pre_host", "--eon_id", 3,
                   "--type", "host", "--comments", "New feature comments",
                   "--visibility", "restricted", "--deactivation", "bad_deactivation"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown value for deactivation. Valid values are: "
                         "dispatch, reboot, rebuild.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
