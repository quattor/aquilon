#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

        command = ["grant_root_access", "--user", "testuser2",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

    def test_220_map_personality_invaliduser(self):
        command = ["grant_root_access", "--user", "testinvaliduser",
                   "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "User testinvaliduser not found", command)

    def test_230_map_personality_invalidpersonality(self):
        command = ["grant_root_access", "--user", "testuser1",
                   "--personality", "unknownpersonality"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality unknownpersonality not found", command)

    def test_240_map_personality_netgroup(self):
        command = ["grant_root_access", "--netgroup", "netgroup1",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

        command = ["grant_root_access", "--netgroup", "netgroup2",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

    def test_250_map_personality_invalidnetgroup(self):
        command = ["grant_root_access", "--netgroup", "testinvalidnetgroup",
                   "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "", command)

    def test_270_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Root Access User: testuser1", command)
        self.matchoutput(out, "Root Access User: testuser2", command)
        self.matchoutput(out, "Root Access Netgroup: netgroup1", command)
        self.matchoutput(out, "Root Access Netgroup: netgroup2", command)

        command =["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/root_users" = list\(\s*'
                               r'"testuser1",\s*'
                               r'"testuser2"',
                          command)
        self.searchoutput(out, r'"/system/root_netgroups" = list\(\s*'
                               r'"netgroup1",\s*'
                               r'"netgroup2"',
                          command)

    def test_310_unmap_personality_user(self):
        command = ["revoke_root_access", "--user", "testuser1",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

    def test_320_unmap_personality_invaliduser(self):
        command = ["revoke_root_access", "--user", "testinvaliduser",
                   "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "User testinvaliduser not found", command)

    def test_330_map_personality_invalidpersonality(self):
        command = ["revoke_root_access", "--user", "testuser2",
                   "--personality", "invalidpersonality"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality invalidpersonality not found", command)

    def test_340_unmap_personality_netgroup(self):
        command = ["revoke_root_access", "--netgroup", "netgroup1",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

    def test_350_unmap_personality_invalidnetgroup(self):
        command = ["grant_root_access", "--netgroup", "testinvalidnetgroup",
                   "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "NetGroupWhiteList testinvalidnetgroup not found", command)

    def test_360_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Root Access User: testuser2", command)
        self.matchoutput(out, "Netgroup: netgroup2", command)

        command =["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/root_users" = list\(\s*'
                               r'"testuser2"',
                          command)
        self.searchoutput(out, r'"/system/root_netgroups" = list\(\s*'
                               r'"netgroup2"',
                          command)

    def test_370_unmap_personality_user(self):
        command = ["revoke_root_access", "--user", "testuser2",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

    def test_380_del_netgroup_stillmapped(self):
        command = ["del", "netgroup_whitelist", "--netgroup", "netgroup2"]
        self.noouttest(command)

    def test_390_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchclean(out, "testuser1", command)
        self.matchclean(out, "testuser2", command)
        self.matchclean(out, "netgroup1", command)
        self.matchclean(out, "netgroup2", command)

        command =["cat", "--archetype=aquilon", "--personality=compileserver"]
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRootAccess)
    unittest.TextTestRunner(verbosity=2).run(suite)

