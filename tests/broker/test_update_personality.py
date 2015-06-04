#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the update personality command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin
from broker.personalitytest import PersonalityTestMixin


class TestUpdatePersonality(VerifyGrnsMixin, PersonalityTestMixin,
                            TestBrokerCommand):
    def test_120_update_cluster_requirement(self):
        command = ["add_personality", "--archetype=aquilon", "--grn=grn:/ms/ei/aquilon/aqd",
                   "--personality=unused", "--host_environment=infra"]
        self.successtest(command)

        command = ["update_personality", "--personality", "unused",
                   "--archetype=aquilon", "--cluster"]
        out = self.successtest(command)

        command = ["del_personality", "--personality", "unused",
                   "--archetype=aquilon"]
        out = self.successtest(command)

    def test_130_add_testovrpersona_dev(self):
        command = ["add_personality", "--archetype=aquilon", "--grn=grn:/ms/ei/aquilon/aqd",
                   "--personality=testovrpersona/dev", "--host_environment=dev"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "override", command)

        self.verifycatpersonality("aquilon", "testovrpersona/dev")

    def test_131_update_config_override(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--config_override"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Config override: enabled", command)

        self.verifycatpersonality("aquilon", "testovrpersona/dev",
                                  config_override=True)

    def test_132_remove_config_override(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--noconfig_override"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "override", command)

        self.verifycatpersonality("aquilon", "testovrpersona/dev")

    def test_133_update_hostenv_testovrpersona(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--host_environment=infra"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Personality aquilon/testovrpersona/dev already has "
                         "its environment set to dev, and cannot be updated.",
                         command)

    def test_139_delete_testovrpersona_dev(self):
        command = ["del_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.successtest(command)

    def test_140_update_owner_grn(self):
        command = ["update_personality", "--personality", "compileserver",
                   "--archetype", "aquilon", "--grn", "grn:/ms/ei/aquilon/ut2"]
        # Some hosts may emit warnings if 'aq make' was not run on them
        self.successtest(command)

    def test_141_verify_owner_grn(self):
        command = ["show_personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/ut2", command)

        command = ["show_host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/ut2", command)

        # unittest02 had a different GRN before, so it should not have been
        # updated
        command = ["show_host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_142_update_owner_grn_nohosts(self):
        command = ["update_personality", "--personality", "compileserver",
                   "--archetype", "aquilon", "--grn", "grn:/ms/ei/aquilon/unittest",
                   "--leave_existing"]
        self.noouttest(command)

    def test_143_verify_update(self):
        command = ["show_personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest", command)

        command = ["show_host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchclean(out, "grn:/ms/ei/aquilon/ut2", command)

        command = ["show_host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_144_verify_cat(self):
        command = ["cat", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/personality/owner_eon_id" = %d;' %
                          self.grns["grn:/ms/ei/aquilon/unittest"], command)

        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com", "--data"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"system/owner_eon_id" = %d;' %
                          self.grns["grn:/ms/ei/aquilon/aqd"], command)

        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.searchclean(out, r'"system/owner_eon_id" = %d;' %
                         self.grns["grn:/ms/ei/aquilon/ut2"], command)

    def test_150_clone_attributes(self):
        self.noouttest(["add_personality", "--personality", "vulcan-1g-clone",
                        "--archetype", "esx_cluster",
                        "--copy_from", "vulcan-10g-server-prod"])

        command = ["show_personality", "--personality", "vulcan-1g-clone",
                   "--archetype", "esx_cluster"]
        out = self.commandtest(command)
        self.matchoutput(out, "Environment: prod", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

        command = ["show_personality", "--personality", "vulcan-1g-clone",
                   "--archetype", "esx_cluster", "--format=proto"]
        personality = self.protobuftest(command, expect=1)[0]
        self.assertEqual(personality.archetype.name, "esx_cluster")
        self.assertEqual(personality.name, "vulcan-1g-clone")
        self.assertEqual(personality.stage, "")
        self.assertEqual(personality.owner_eonid, self.grns["grn:/ms/ei/aquilon/aqd"])
        self.assertEqual(personality.host_environment, "prod")

    def test_159_cleanup_clone(self):
        self.noouttest(["del_personality", "--personality", "vulcan-1g-clone",
                        "--archetype", "esx_cluster"])

    def test_160_update_comments(self):
        self.noouttest(["update_personality", "--personality", "utpersonality/dev",
                        "--archetype", "aquilon",
                        "--comments", "New personality comments"])

    def test_161_verify_update(self):
        command = ["show_personality", "--personality=utpersonality/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out, "Comments: New personality comments", command)

    def test_165_clear_comments(self):
        self.noouttest(["update_personality", "--personality", "utpersonality/dev",
                        "--archetype", "aquilon", "--comments", ""])

    def test_166_verify_clear(self):
        command = ["show_personality", "--personality=utpersonality/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Comments", command)

    def test_170_make_staged(self):
        self.noouttest(["update_personality", "--personality", "compileserver",
                        "--archetype", "aquilon", "--staged"])

    def test_171_show_current(self):
        command = ["show_personality", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Stage: current", command)

    def test_171_cat_current(self):
        self.verifycatpersonality("aquilon", "compileserver", stage="current")

    def test_172_show_next(self):
        command = ["show_personality", "--personality", "unixeng-test",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out, "Stage: next", command)

    def test_172_cat_next(self):
        self.verifycatpersonality("aquilon", "compileserver", stage="next")

    def test_174_delete_next(self):
        self.noouttest(["del_personality", "--personality", "unixeng-test",
                        "--archetype", "aquilon", "--personality_stage", "next"])

    def test_175_verify_next_gone(self):
        command = ["show_personality", "--personality", "unixeng-test",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/unixeng-test does not have "
                         "stage next.", command)

    def test_178_make_unstaged(self):
        self.noouttest(["update_personality", "--personality", "compileserver",
                        "--archetype", "aquilon", "--unstaged"])

    def test_179_verify_unstaged(self):
        command = ["show_personality", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Stage:", command)

    def test_179_cat_unstaged(self):
        self.verifycatpersonality("aquilon", "compileserver")

    def test_200_update_cluster_inuse(self):
        command = ["update_personality", "--personality=vulcan-10g-server-prod",
                   "--archetype=esx_cluster",
                   "--cluster",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality esx_cluster/vulcan-10g-server-prod is in use", command)

    def test_200_missing_personality(self):
        command = ["update_personality", "--archetype", "aquilon",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype aquilon not found.", command)

    def test_200_missing_personality_stage(self):
        command = ["update_personality", "--archetype", "aquilon",
                   "--personality", "nostage",
                   "--personality_stage", "previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality aquilon/nostage does not have stage "
                         "previous.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdatePersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
