#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
"""Module for testing the add personality --copy_from command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin

GRN = "grn:/ms/ei/aquilon/aqd"


class TestCopyPersonality(VerifyGrnsMixin, TestBrokerCommand):

    def test_100_restore_utunused_comments(self):
        self.noouttest(["update_personality", "--archetype", "aquilon",
                        "--personality", "utunused/dev",
                        "--comments", "New personality comments"])

    def test_110_add_utunused_clone(self):
        command = ["add_personality", "--personality", "utunused-clone/dev",
                   "--archetype", "aquilon", "--copy_from", "utunused/dev"]
        out = self.statustest(command)
        self.matchoutput(out, "Personality aquilon/utunused/dev has "
                         "config_override set", command)

    def test_111_verify_utunused_clone(self):
        command = ["show_personality", "--personality", "utunused-clone/dev",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utunused-clone/dev Archetype: aquilon",
                         command)
        self.matchoutput(out, "Environment: dev", command)
        self.matchclean(out, "Stage:", command)
        self.matchoutput(out, "Comments: New personality comments", command)
        self.matchoutput(out, "Owned by GRN: %s" % GRN, command)
        self.matchoutput(out, "Used by GRN: %s [target: esp]" % GRN, command)
        self.matchclean(out, "Config override", command)

    def test_115_show_map_archetype(self):
        command = ["show_map", "--archetype=aquilon", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: utunused-clone/dev "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def test_120_clone_esx_attributes(self):
        self.noouttest(["add_personality", "--personality", "vulcan-1g-clone",
                        "--archetype", "esx_cluster",
                        "--copy_from", "vulcan-10g-server-prod"])

    def test_121_verify_esx_clone(self):
        command = ["show_personality", "--personality", "vulcan-1g-clone",
                   "--archetype", "esx_cluster"]
        out = self.commandtest(command)
        self.matchoutput(out, "Environment: prod", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)
        self.matchoutput(out,
                         "VM host capacity function: {'memory': (memory - 1500) * 0.94}",
                         command)

    def test_121_verify_esx_clone_proto(self):
        command = ["show_personality", "--personality", "vulcan-1g-clone",
                   "--archetype", "esx_cluster", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        self.assertEqual(personality.archetype.name, "esx_cluster")
        self.assertEqual(personality.name, "vulcan-1g-clone")
        self.assertEqual(personality.stage, "")
        self.assertEqual(personality.owner_eonid, self.grns["grn:/ms/ei/aquilon/aqd"])
        self.assertEqual(personality.host_environment, "prod")
        self.assertEqual(personality.vmhost_capacity_function, "{'memory': (memory - 1500) * 0.94}")

    def test_130_clone_inventory(self):
        self.noouttest(["add_personality", "--personality", "inventory-clone",
                        "--copy_from", "inventory", "--archetype", "aquilon",
                        "--staged"])

    def test_131_verify_clone_features(self):
        command = ["show", "personality", "--personality", "inventory-clone",
                   "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: post_host [post_personality]",
                         command)

    def test_131_verify_clone_features_proto(self):
        command = ["show", "personality", "--personality", "inventory-clone",
                   "--personality_stage", "next", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        feature = personality.features[0]
        self.assertEqual(feature.name, "post_host")
        self.assertEqual(feature.type, "host")
        self.assertEqual(feature.post_personality, True)
        self.assertEqual(feature.interface_name, "")
        self.assertEqual(feature.model.name, "")
        self.assertEqual(feature.model.vendor, "")

    def test_131_verify_show_feature(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.searchoutput(out, r"Bound to: Personality aquilon/inventory$",
                          command)
        self.searchoutput(out, r"Bound to: Personality aquilon/inventory-clone@next$",
                          command)

    def test_131_verify_clone_routes(self):
        gw = self.net["routing1"].usable[-1]
        command = ["show", "network", "--ip", self.net["routing1"].ip]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Static Route: 192\.168\.248\.0/24 gateway %s'
                          r'\s*Personality: inventory-clone Archetype: aquilon$'
                          r'\s*Stage: next$' % gw,
                          command)

    def test_140_copy_stage(self):
        command = ["add_personality", "--personality", "utpers-dev-clone",
                   "--archetype", "aquilon",
                   "--copy_from", "utpers-dev", "--copy_stage", "next"]
        self.noouttest(command)

        command = ["show_diff", "--archetype", "aquilon",
                   "--personality", "utpers-dev", "--personality_stage", "next",
                   "--other", "utpers-dev-clone", "--other_stage", "next"]
        self.noouttest(command)

        command = ["show_diff", "--archetype", "aquilon",
                   "--personality", "utpers-dev", "--personality_stage", "current",
                   "--other", "utpers-dev-clone", "--other_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "missing Parameters in Personality aquilon/utpers-dev@current:",
                         command)

    def test_200_copy_missing_stage(self):
        command = ["add_personality", "--personality", "copy-test",
                   "--archetype", "aquilon", "--copy_from", "nostage"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/nostage does not have "
                         "stage current.", command)

    def test_200_copy_bad_stage(self):
        command = ["add_personality", "--personality", "copy-test",
                   "--archetype", "aquilon", "--copy_from", "nostage",
                   "--copy_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

    def test_800_cleanup(self):
        self.noouttest(["del_personality", "--archetype", "aquilon",
                        "--personality", "utunused-clone/dev"])
        self.noouttest(["del_personality", "--archetype", "aquilon",
                        "--personality", "utpers-dev-clone"])
        self.noouttest(["del_personality", "--archetype", "aquilon",
                        "--personality", "inventory-clone"])
        self.noouttest(["del_personality", "--archetype", "esx_cluster",
                        "--personality", "vulcan-1g-clone"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCopyPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
