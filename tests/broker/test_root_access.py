#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Module for testing GRN support."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestRootAccess(TestBrokerCommand):
    def test_100_add_netgroup(self):
        command = ["add", "netgroup_whitelist", "--netgroup", "netgroup1"]
        self.noouttest(command)

        command = ["add", "netgroup_whitelist", "--netgroup", "netgroup2"]
        self.noouttest(command)

    def test_110_verify_add_netgroup(self):
        command = ["show", "netgroup_whitelist", "--netgroup", "netgroup1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Netgroup: netgroup1", command)

        command = ["show", "netgroup_whitelist", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Netgroup: netgroup1", command)
        self.matchoutput(out, "Netgroup: netgroup2", command)

    def test_210_map_personality_user(self):
        command = ["grant_root_access", "--user", "testuser1",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

        command = ["grant_root_access", "--user", "testuser2",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

    def test_220_map_personality_invaliduser(self):
        command = ["grant_root_access", "--user", "testinvaliduser",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "User testinvaliduser not found", command)

    def test_225_map_personality_invalidjustification(self):
        command = ["grant_root_access", "--user", "testuser1",
                   "--personality", "unknownpersonality", "--justification", "foo"]
 	out = self.badrequesttest(command)
        self.matchoutput(out, "Failed to parse the justification: expected tcm=NNNNNNNNN or sn=XXXNNNNN", command)

    def test_230_map_personality_invalidpersonality(self):
        command = ["grant_root_access", "--user", "testuser1",
                   "--personality", "unknownpersonality", "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality unknownpersonality not found", command)

    def test_240_map_personality_netgroup(self):
        command = ["grant_root_access", "--netgroup", "netgroup1",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

        command = ["grant_root_access", "--netgroup", "netgroup2",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

    def test_250_map_personality_invalidnetgroup(self):
        command = ["grant_root_access", "--netgroup", "testinvalidnetgroup",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "", command)

    def test_270_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Root Access User: testuser1", command)
        self.matchoutput(out, "Root Access User: testuser2", command)
        self.matchoutput(out, "Root Access Netgroup: netgroup1", command)
        self.matchoutput(out, "Root Access Netgroup: netgroup2", command)

        command = ["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/root_users" = list\(\s*'
                               r'"testuser1",\s*'
                               r'"testuser2"\s*\);',
                          command)
        self.searchoutput(out, r'"/system/root_netgroups" = list\(\s*'
                               r'"netgroup1",\s*'
                               r'"netgroup2"\s*\);',
                          command)

    def test_310_unmap_personality_user(self):
        command = ["revoke_root_access", "--user", "testuser1",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

    def test_320_unmap_personality_invaliduser(self):
        command = ["revoke_root_access", "--user", "testinvaliduser",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "User testinvaliduser not found", command)

    def test_330_map_personality_invalidpersonality(self):
        command = ["revoke_root_access", "--user", "testuser2",
                   "--personality", "invalidpersonality", "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality invalidpersonality not found", command)

    def test_340_unmap_personality_netgroup(self):
        command = ["revoke_root_access", "--netgroup", "netgroup1",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

    def test_350_unmap_personality_invalidnetgroup(self):
        command = ["grant_root_access", "--netgroup", "testinvalidnetgroup",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "NetGroupWhiteList testinvalidnetgroup not found", command)

    def test_360_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Root Access User: testuser2", command)
        self.matchoutput(out, "Netgroup: netgroup2", command)

        command = ["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/root_users" = list\(\s*'
                               r'"testuser2"\s*\);',
                          command)
        self.searchoutput(out, r'"/system/root_netgroups" = list\(\s*'
                               r'"netgroup2"\s*\);',
                          command)

    def test_370_unmap_personality_user(self):
        command = ["revoke_root_access", "--user", "testuser2",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

    def test_380_del_netgroup_stillmapped(self):
        command = ["del", "netgroup_whitelist", "--netgroup", "netgroup2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Netgroup netgroup2 used by following and cannot be deleted :"
                              " Personality aquilon/compileserver",
                         command)

        command = ["revoke_root_access", "--netgroup", "netgroup2",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)

        command = ["del", "netgroup_whitelist", "--netgroup", "netgroup2"]
        out = self.noouttest(command)

    def test_390_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchclean(out, "testuser1", command)
        self.matchclean(out, "testuser2", command)
        self.matchclean(out, "netgroup1", command)
        self.matchclean(out, "netgroup2", command)

        command = ["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.matchclean(out, "testuser1", command)
        self.matchclean(out, "testuser2", command)
        self.matchclean(out, "netgroup1", command)
        self.matchclean(out, "netgroup2", command)

    def test_410_del_netgroup(self):
        command = ["del", "netgroup_whitelist", "--netgroup", "netgroup1"]
        self.noouttest(command)

    def test_420_verify_del_netgroup(self):
        command = ["show", "netgroup_whitelist", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "netgroup1", command)
        self.matchclean(out, "netgroup2", command)

    def test_430_del_netgroup_notfound(self):
        command = ["del", "netgroup_whitelist", "--netgroup", "notfound"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "NetGroupWhiteList notfound not found", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRootAccess)
    unittest.TextTestRunner(verbosity=2).run(suite)
