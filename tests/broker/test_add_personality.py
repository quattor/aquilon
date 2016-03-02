#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the add personality command."""

from collections import defaultdict

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin
from broker.personalitytest import PersonalityTestMixin

GRN = "grn:/ms/ei/aquilon/aqd"


class TestAddPersonality(VerifyGrnsMixin, PersonalityTestMixin,
                         TestBrokerCommand):
    def test_100_add_utpersonality(self):
        # Unused personality with basic settings
        command = ["add_personality", "--personality=utunused/dev",
                   "--archetype=aquilon", "--grn=%s" % GRN, "--config_override",
                   "--host_environment=dev",
                   "--comments", "Some personality comments"]
        self.noouttest(command)
        self.verifycatpersonality("aquilon", "utunused/dev", True, "dev",
                                  grn=GRN)
        for plenary in ("pre_feature", "post_feature", "espinfo"):
            self.check_plenary_exists("aquilon", "personality",
                                      "utunused/dev", plenary)

    def test_105_verify_utpersonality(self):
        command = ["show_personality", "--personality=utunused/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utunused/dev Archetype: aquilon",
                         command)
        self.matchoutput(out, "Config override: enabled", command)
        self.matchoutput(out, "Environment: dev", command)
        self.matchclean(out, "Stage:", command)
        self.matchoutput(out, "Comments: Some personality comments", command)
        self.matchoutput(out, "Owned by GRN: %s" % GRN, command)
        self.matchoutput(out, "Used by GRN: %s [target: esp]" % GRN, command)
        self.matchclean(out, "inventory", command)

    def test_105_verify_utpersonality_proto(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=utunused/dev", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        self.assertEqual(personality.archetype.name, "aquilon")
        self.assertEqual(personality.name, "utunused/dev")
        self.assertEqual(personality.stage, "")
        self.assertEqual(personality.config_override, True)
        self.assertEqual(personality.cluster_required, False)
        self.assertEqual(personality.comments, "Some personality comments")
        self.assertEqual(personality.owner_eonid, self.grns[GRN])
        self.assertEqual(personality.host_environment, "dev")

    def test_120_add_netinfra(self):
        command = ["add_personality", "--personality=generic",
                   "--archetype=netinfra", "--eon_id=10",
                   "--host_environment=dev"]
        self.noouttest(command)

    def test_125_add_utpers_dev(self):
        command = ["add_personality", "--personality=utpers-dev",
                   "--archetype=aquilon", "--eon_id=2",
                   "--host_environment=dev", "--staged"]
        self.noouttest(command)
        for plenary in ("pre_feature", "post_feature", "espinfo"):
            self.check_plenary_exists("aquilon", "personality",
                                      "utpers-dev+next", plenary)
        self.verifycatpersonality("aquilon", "utpers-dev", stage="next")
        # The basic parameter set needs to be initialized for further tests
        self.setup_personality("aquilon", "utpers-dev")

    def test_126_verify_utpers_dev(self):
        command = ["show_personality", "--personality", "utpers-dev",
                   "--archetype", "aquilon"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/utpers-dev does not have "
                         "stage current.", command)

    def test_126_verify_utpers_dev_next(self):
        command = ["show_personality", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out, "Stage: next", command)

        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out, "espinfo", command)

    def test_130_add_windows_desktop(self):
        command = ["add", "personality", "--personality", "desktop",
                   "--archetype", "windows", "--grn", "grn:/ms/windows/desktop",
                   "--host_environment", "dev"]
        self.noouttest(command)
        self.verifycatpersonality("windows", "desktop")

    def test_135_verify_windows_desktop(self):
        command = "show_personality --personality desktop --archetype windows"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: desktop Archetype: windows",
                         command)

    def test_140_add_badpersonality(self):
        # This personality is 'bad' because no required parameters will be set
        # up for it, so anything using it will fail to compile.
        command = ["add_personality", "--personality=badpersonality",
                   "--host_environment=dev",
                   "--archetype=aquilon", "--eon_id=2"]
        self.noouttest(command)

    def test_141_verify_badpersonality(self):
        command = ["show_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: badpersonality Archetype: aquilon",
                         command)

    def test_145_add_badpersonality2(self):
        # This personality is double 'bad'... there will be a required
        # service for the personality that has no instances.
        command = ["add_personality", "--personality=badpersonality2",
                   "--host_environment=dev",
                   "--archetype=aquilon", "--eon_id=2"]
        self.noouttest(command)

    def test_146_verify_badpersonality2(self):
        command = ["show_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Personality: badpersonality2 Archetype: aquilon",
                         command)

    def test_150_add_selective_name_match_env(self):
        command = ["add_personality", "--personality", "ec-infra-auth",
                   "--host_environment", "infra",
                   "--archetype", "vmhost", "--eon_id=2"]
        self.successtest(command)

    def test_155_add_camelcase(self):
        self.noouttest(["add_personality", "--personality", "CaMeLcAsE",
                        "--host_environment=dev", "--archetype", "aquilon",
                        "--eon_id=2"])
        self.check_plenary_exists("aquilon", "personality", "camelcase",
                                  "config")
        self.check_plenary_gone("aquilon", "personality", "CaMeLcAsE", "config",
                                directory_gone=True)

    def test_160_add_esx_server(self):
        command = ["add_personality", "--cluster_required", "--eon_id=2",
                   "--host_environment=dev",
                   "--personality=esx_server", "--archetype=vmhost"]
        self.noouttest(command)
        self.verifycatpersonality("vmhost", "esx_server",
                                  grn="grn:/ms/ei/aquilon/aqd")
        command = ["show_personality", "--personality=esx_server",
                   "--archetype=vmhost"]
        out = self.commandtest(command)
        self.matchoutput(out, "Requires clustered hosts", command)

        command = ["add_personality", "--eon_id=2", "--host_environment=dev",
                   "--personality=esx_server", "--archetype=esx_cluster"]
        self.noouttest(command)
        self.verifycatpersonality("esx_cluster", "esx_server")

    def test_165_add_esx_standalone(self):
        # Can't use create_personality() here, because the --cluster_required
        # flag is intentionally missing.
        command = ["add_personality", "--personality=esx_standalone",
                   "--host_environment=dev",
                   "--archetype=vmhost", "--eon_id=2"]
        self.noouttest(command)
        self.verifycatpersonality("vmhost", "esx_standalone",
                                  grn="grn:/ms/ei/aquilon/aqd")
        command = ["show_personality", "--personality=esx_standalone",
                   "--archetype=vmhost"]
        out = self.commandtest(command)
        self.matchclean(out, "Requires clustered hosts", command)

    def test_166_add_esx_nostage(self):
        command = ["add_personality", "--personality", "nostage",
                   "--archetype", "vmhost", "--cluster_required",
                   "--eon_id", 2, "--host_environment", "dev",
                   "--staged"]
        self.noouttest(command)

    def test_170_add_grid_personality(self):
        command = ["add_personality", "--eon_id=2", "--host_environment=dev",
                   "--personality=hadoop", "--archetype=gridcluster"]
        self.noouttest(command)
        self.verifycatpersonality("gridcluster", "hadoop")

    def test_171_add_ha_personality(self):
        self.create_personality("hacluster", "hapersonality",
                                grn="grn:/ms/ei/aquilon/aqd")
        self.verifycatpersonality("hacluster", "hapersonality")

    def test_172_add_generic(self):
        for archetype in ["aurora", "f5", "filer", "vmhost", "windows"]:
            self.noouttest(["add", "personality", "--personality", "generic",
                            "--archetype", archetype,
                            "--host_environment", "prod",
                            "--grn", "grn:/ms/ei/aquilon/unittest"])

    def test_173_add_aquilon_personalities(self):
        personalities = {
            'compileserver': {},
            'inventory': {},
            'unixeng-test': {'staged': True},
            'nostage': {'staged': True},
            'clustered': {'cluster_required': True},
            'utpers-prod': {'environment': 'prod'},
        }
        for personality, kwargs in personalities.items():
            self.create_personality("aquilon", personality, **kwargs)

    def test_200_invalid_personality_name(self):
        command = ["add_personality", "--personality", "this is a bad; name",
                   "--host_environment=dev",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality name 'this is a bad; name' is "
                         "not valid", command)

    def test_200_invalid_environment(self):
        command = ["add_personality", "--personality", "invalidenvironment",
                   "--host_environment", "badenv",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown host environment 'badenv'. The valid"
                              " values are: dev, infra, legacy, prod, qa, uat",
                         command)

    def test_200_environment_mismatch_1(self):
        command = ["add_personality", "--personality", "test/dev",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test/dev' "
                              "does not match the host environment 'qa'",
                         command)

    def test_200_environment_mismatch_2(self):
        command = ["add_personality", "--personality", "test-dev",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test-dev' "
                              "does not match the host environment 'qa'",
                         command)

    def test_200_environment_mismatch_3(self):
        command = ["add_personality", "--personality", "test-qa-dev",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test-qa-dev' "
                              "does not match the host environment 'qa'",
                         command)

    def test_200_environment_mismatch_4(self):
        command = ["add_personality", "--personality", "test-qa-DEV",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test-qa-DEV' "
                              "does not match the host environment 'qa'",
                         command)

    def test_200_no_default_environment(self):
        command = ["add_personality", "--eon_id=2", "--archetype=aquilon",
                   "--personality=no-environment"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Default environment is not configured for archetype "
                         "aquilon, please specify --host_environment.",
                         command)

    def test_200_add_legacy(self):
        command = ["add_personality", "--personality=testlegacy",
                   "--archetype=aquilon", "--grn=%s" % GRN,
                   "--host_environment=legacy"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Legacy is not a valid environment for a new personality.",
                         command)

    def test_200_duplicate(self):
        command = ["add_personality", "--personality", "inventory",
                   "--host_environment=dev",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality inventory, archetype aquilon "
                         "already exists.", command)

    def test_300_show_personality_all(self):
        command = "show_personality --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utunused/dev Archetype: aquilon",
                         command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)

    def test_300_show_personality_all_proto(self):
        command = "show_personality --all --format=proto"
        personalities = self.protobuftest(command.split(" "))
        archetypes = defaultdict(dict)
        for personality in personalities:
            archetype = personality.archetype.name
            if personality.name in archetypes[archetype]:
                archetypes[archetype][personality.name][personality.stage] = personality
            else:
                archetypes[archetype][personality.name] = {personality.stage: personality}
        self.assertTrue("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.assertTrue("utunused/dev" in archetypes["aquilon"],
                        "No aquilon/utunused/dev in personality list.")
        self.assertTrue("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.assertTrue("generic" in archetypes["aurora"],
                        "No aurora/generic in personality list.")
        self.assertFalse("current" in
                         archetypes["aquilon"]["utunused/dev"])
        self.assertFalse("current" in archetypes["aquilon"]["utpers-dev"])
        self.assertTrue("next" in archetypes["aquilon"]["utpers-dev"])
        self.assertFalse("current" in archetypes["aquilon"]["unixeng-test"])
        self.assertTrue("next" in archetypes["aquilon"]["unixeng-test"])

    def test_300_show_personality_archetype(self):
        command = "show_personality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utunused/dev Archetype: aquilon",
                         command)
        self.matchoutput(out, "Personality: inventory Archetype: aquilon",
                         command)
        self.matchclean(out, "aurora", command)

    def test_300_show_personality_name(self):
        command = "show_personality --personality generic"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out, "Personality: generic Archetype: windows",
                         command)

    def test_400_show_archetype_unavailable(self):
        command = "show_personality --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def test_400_show_archetype_unavailable2(self):
        command = ["show_personality",
                   "--archetype", "archetype-does-not-exist",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def test_400_show_personality_unavailable(self):
        command = ["show_personality", "--archetype", "aquilon",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype aquilon not found.", command)

    def test_400_show_personality_unavailable2(self):
        command = ["show_personality",
                   "--personality", "personality-does-not-exist"]
        self.noouttest(command)

    def test_400_show_missing_stage(self):
        command = ["show_personality", "--personality", "nostage",
                   "--archetype", "aquilon"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/nostage does not have "
                         "stage current.", command)

    def test_400_show_bad_stage(self):
        command = ["show_personality", "--personality", "nostage",
                   "--archetype", "aquilon",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

    def test_400_cat_missing_stage(self):
        command = ["cat", "--personality", "nostage", "--archetype", "aquilon"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/nostage does not have "
                         "stage current.", command)

    def test_400_cat_bad_stage(self):
        command = ["cat", "--personality", "nostage", "--archetype", "aquilon",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

    def test_800_promote_unixeng_test(self):
        self.noouttest(["promote", "--personality", "unixeng-test",
                        "--archetype", "aquilon"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
