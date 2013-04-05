#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin


class TestUpdatePersonality(VerifyGrnsMixin, TestBrokerCommand):

    def test_200_invalid_function(self):
        """ Verify that the list of built-in functions is restricted """
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "locals()"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name 'locals' is not defined", command)

    def test_200_invalid_type(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "memory - 100"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The function should return a dictonary.", command)

    def test_200_invalid_dict(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': 'bar'}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The function should return a dictionary with all "
                         "keys being strings, and all values being numbers.",
                         command)

    def test_200_missing_memory(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'foo': 5}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The memory constraint is missing from the returned "
                         "dictionary.", command)

    def test_200_not_enough_memory(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': memory / 4}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Validation failed for the following clusters:",
                         command)
        self.matchoutput(out,
                         "ESX Cluster utecl1 is over capacity regarding memory",
                         command)

    def test_100_update_capacity(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': (memory - 1500) * 0.94}"]
        self.noouttest(command)

    def test_110_update_overcommit(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_overcommit_memory", 1.04]
        self.noouttest(command)

    def test_115_verify_update_capacity(self):
        command = ["show_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "VM host capacity function: {'memory': (memory - 1500) * 0.94}",
                         command)
        self.matchoutput(out, "VM host overcommit factor: 1.04", command)

    def test_200_update_cluster_inuse(self):
        command = ["update_personality", "--personality=vulcan-1g-desktop-prod",
                   "--archetype=esx_cluster",
                   "--cluster"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The personality vulcan-1g-desktop-prod is in use", command)

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

        command = ["cat", "--archetype=aquilon", "--personality=testovrpersona/dev"]
        out = self.commandtest(command)
        self.matchclean(out, 'override', command)

    def test_131_update_config_override(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--config_override"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Config override: enabled", command)

        command = ["cat", "--archetype=aquilon", "--personality=testovrpersona/dev"]
        out = self.commandtest(command)
        self.matchoutput(out, 'include { "features/personality/config_override/config" }',
                         command)

    def test_132_remove_config_override(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--noconfig_override"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "override", command)

        command = ["cat", "--archetype=aquilon", "--personality=testovrpersona/dev"]
        self.matchclean(out, 'override', command)

    def test_133_update_hostenv_testovrpersona(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                    "--archetype=aquilon", "--host_environment=dev"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The personality 'testovrpersona/dev' already has env set to 'dev' and cannot be update",
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
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/ut2", command)

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
        self.searchoutput(out, r'"system/owner_eon_id" = %d;' %
                          self.grns["grn:/ms/ei/aquilon/ut2"], command)

    def test_150_update_hostenv_infra(self):
        command = ["add_personality", "--archetype=windows", "--grn=grn:/ms/ei/aquilon/aqd",
                   "--personality=prod-perim", "--host_environment=legacy"]
        self.successtest(command)

        command = ["update_personality", "--personality=prod-perim",
                    "--archetype=windows", "--host_environment=infra"]
        out = self.successtest(command)

        command = ["show_personality", "--personality=prod-perim",
                   "--archetype=windows"]
        out = self.commandtest(command)
        self.matchoutput(out, "Environment: infra", command)

        command = ["del_personality", "--archetype=windows", "--personality=prod-perim"]
        self.successtest(command)

    def test_155_update_hostenv_prod(self):
        command = ["update_personality", "--personality=desktop",
                    "--archetype=windows", "--host_environment=prod"]
        out = self.successtest(command)

        command = ["show_personality", "--personality=desktop",
                   "--archetype=windows"]
        out = self.commandtest(command)
        self.matchoutput(out, "Environment: prod", command)

        command = ["cat", "--personality=desktop"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/personality/host_environment" = "prod";', command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdatePersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
