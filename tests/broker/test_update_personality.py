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
"""Module for testing the update personality command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin
from broker.personalitytest import PersonalityTestMixin


class TestUpdatePersonality(VerifyGrnsMixin, PersonalityTestMixin,
                            TestBrokerCommand):
    def test_100_update_capacity(self):
        command = ["update_personality", "--personality", "vulcan-10g-server-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': (memory - 1500) * 0.94}",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def test_115_verify_update_capacity(self):
        command = ["show_personality", "--personality", "vulcan-10g-server-prod",
                   "--archetype", "esx_cluster"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "VM host capacity function: {'memory': (memory - 1500) * 0.94}",
                         command)

    def test_120_update_basic_attributes(self):
        command = ["update_personality", "--personality", "utunused/dev",
                   "--archetype=aquilon",
                   "--cluster_required",
                   "--noconfig_override",
                   "--comments", "New personality comments"]
        self.successtest(command)

    def test_121_verify_updates(self):
        command = ["show_personality", "--personality=utunused/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)

        self.matchoutput(out, "Personality: utunused/dev Archetype: aquilon",
                         command)
        self.matchoutput(out, "Comments: New personality comments", command)
        self.matchoutput(out, "Requires clustered hosts", command)
        self.matchclean(out, "override", command)

        self.verifycatpersonality("aquilon", "utunused/dev")

    def test_125_restore_utpersonality_dev(self):
        # Well, except the comments, which are removed
        command = ["update_personality", "--personality", "utunused/dev",
                   "--archetype=aquilon",
                   "--nocluster_required",
                   "--config_override",
                   "--comments", ""]
        self.successtest(command)

    def test_126_verify_utpersonality_dev(self):
        command = ["show_personality", "--personality=utunused/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Requires clustered hosts", command)
        self.matchoutput(out, "Config override: enabled", command)

        self.verifycatpersonality("aquilon", "utunused/dev",
                                  config_override=True)

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
        self.check_plenary_exists("aquilon", "personality",
                                  "compileserver+next", "espinfo")
        self.noouttest(["update_personality", "--personality", "compileserver",
                        "--archetype", "aquilon", "--unstaged"])
        self.check_plenary_gone("aquilon", "personality",
                                "compileserver+next", "espinfo")

    def test_179_verify_unstaged(self):
        command = ["show_personality", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Stage:", command)

    def test_179_cat_unstaged(self):
        self.verifycatpersonality("aquilon", "compileserver")

    def test_200_invalid_function(self):
        """ Verify that the list of built-in functions is restricted """
        command = ["update_personality", "--personality", "vulcan-10g-server-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "locals()",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name 'locals' is not defined", command)

    def test_200_invalid_type(self):
        command = ["update_personality", "--personality", "vulcan-10g-server-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "memory - 100",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The function should return a dictonary.", command)

    def test_200_invalid_dict(self):
        command = ["update_personality", "--personality", "vulcan-10g-server-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': 'bar'}",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The function should return a dictionary with all "
                         "keys being strings, and all values being numbers.",
                         command)

    def test_200_missing_memory(self):
        command = ["update_personality", "--personality", "vulcan-10g-server-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'foo': 5}",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The memory constraint is missing from the returned "
                         "dictionary.", command)

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

    def test_200_change_environment(self):
        command = ["update_personality", "--personality=utunused/dev",
                   "--archetype=aquilon", "--host_environment=infra"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Personality aquilon/utunused/dev already has "
                         "its environment set to dev, and cannot be updated.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdatePersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
