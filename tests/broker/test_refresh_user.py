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
"""Module for testing the refresh user principals command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestRefreshUser(TestBrokerCommand):

    def test_100_verify_testuser3(self):
        command = ["show_user", "--username", "testuser3"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser3$', command)
        self.searchoutput(out, r'Uid: 2361$', command)
        self.searchoutput(out, r'Gid: 654$', command)
        self.searchoutput(out, r'Full Name: test user$', command)
        self.searchoutput(out, r'Home Dir: /tmp$', command)

    def test_100_verify_testuser4(self):
        command = ["show_user", "--username", "testuser4"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser4$', command)
        self.searchoutput(out, r'Uid: 2362$', command)
        self.searchoutput(out, r'Gid: 654$', command)
        self.searchoutput(out, r'Full Name: test user$', command)
        self.searchoutput(out, r'Home Dir: /tmp$', command)

    def test_110_grant_testuser4_root(self):
        command = ["grant_root_access", "--user", "testuser4",
                   "--personality", "compileserver", "--justification", "tcm=12345678"]
        self.successtest(command)

    def test_111_verify_testuser4_root(self):
        command = ["show_personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Root Access User: testuser4", command)

        command = ["cat", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "testuser4", command)

    def test_200_refresh(self):
        command = ["refresh", "user"]
        err = self.statustest(command)
        self.matchoutput(err, "Added 2, deleted 1, updated 1 users.", command)

    def test_210_verify_all(self):
        command = ["show_user", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "testuser1", command)
        self.matchoutput(out, "testuser2", command)
        self.matchoutput(out, "testuser3", command)
        self.matchclean(out, "testuser4", command)

    def test_210_verify_testuser1(self):
        command = ["show_user", "--username", "testuser1"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser1$', command)
        self.searchoutput(out, r'Uid: 1234$', command)
        self.searchoutput(out, r'Gid: 423$', command)
        self.searchoutput(out, r'Full Name: test user 1$', command)
        self.searchoutput(out, r'Home Dir: /tmp$', command)

    def test_210_verify_testuser3(self):
        command = ["show_user", "--username", "testuser3"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser3$', command)
        self.searchoutput(out, r'Uid: 1236$', command)
        self.searchoutput(out, r'Gid: 655$', command)
        self.searchoutput(out, r'Full Name: test user 3$', command)
        self.searchoutput(out, r'Home Dir: /tmp/foo$', command)

    def test_220_verify_testuser4_root_gone(self):
        command = ["show_personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchclean(out, "testuser4", command)

        command = ["cat", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "testuser4", command)

    def test_300_refresh_again(self):
        command = ["refresh", "user", "--incremental"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Added 0, deleted 0, updated 0 users.", command)

    def test_310_verify_testuser1_again(self):
        command = ["show_user", "--username", "testuser1"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser1$', command)
        self.searchoutput(out, r'Uid: 1234$', command)
        self.searchoutput(out, r'Gid: 423$', command)
        self.searchoutput(out, r'Full Name: test user 1$', command)
        self.searchoutput(out, r'Home Dir: /tmp$', command)

    def test_310_verify_testuser3_again(self):
        command = ["show_user", "--username", "testuser3"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser3$', command)
        self.searchoutput(out, r'Uid: 1236$', command)
        self.searchoutput(out, r'Gid: 655$', command)
        self.searchoutput(out, r'Full Name: test user 3$', command)
        self.searchoutput(out, r'Home Dir: /tmp/foo$', command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshUser)
    unittest.TextTestRunner(verbosity=2).run(suite)
