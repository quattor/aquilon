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
"""Module for testing the add user command."""

import pwd
import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddUser(TestBrokerCommand):
    def test_100_add_current_user(self):
        pwrec = pwd.getpwuid(os.getuid())
        # Use artificial values for some parameters for easier testing
        self.noouttest(["add_user", "--username", pwrec[0], "--uid", 1000,
                        "--gid", 1000, "--full_name", "Current user",
                        "--home_directory", pwrec[5]])

    def test_101_verify_current(self):
        pwrec = pwd.getpwuid(os.getuid())
        command = ["show_user", "--username", pwrec[0]]
        out = self.commandtest(command)
        self.matchoutput(out, "User: %s" % pwrec[0], command)
        self.matchoutput(out, "UID: 1000", command)
        self.matchoutput(out, "GID: 1000", command)
        self.matchoutput(out, "Full Name: Current user", command)
        self.matchoutput(out, "Home Directory: %s" % pwrec[5], command)

    def test_110_add_testuser3(self):
        self.noouttest(["add_user", "--username", "testuser3", "--uid", 2361,
                        "--gid", 654, "--full_name", "test user",
                        "--home_directory", "/tmp"])

    def test_111_verify_testuser3(self):
        command = ["show_user", "--username", "testuser3"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser3$', command)
        self.searchoutput(out, r'UID: 2361$', command)
        self.searchoutput(out, r'GID: 654$', command)
        self.searchoutput(out, r'Full Name: test user$', command)
        self.searchoutput(out, r'Home Directory: /tmp$', command)

    def test_115_add_testuser4(self):
        self.noouttest(["add_user", "--username", "testuser4", "--autouid",
                        "--gid", 654, "--full_name", "test user",
                        "--home_directory", "/tmp"])

    def test_116_verify_testuser4(self):
        command = ["show_user", "--username", "testuser4"]
        out = self.commandtest(command)
        self.searchoutput(out, r'User: testuser4$', command)
        self.searchoutput(out, r'UID: 2362$', command)
        self.searchoutput(out, r'GID: 654$', command)
        self.searchoutput(out, r'Full Name: test user$', command)
        self.searchoutput(out, r'Home Directory: /tmp$', command)

    def test_200_duplicate_name(self):
        command = ["add_user", "--username", "testuser3", "--autouid",
                   "--gid", 1001, "--full_name", "Other user",
                   "--home_directory", "/tmp"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User testuser3 already exists.", command)

    def test_200_duplicate_uid(self):
        command = ["add_user", "--username", "another", "--uid", 2362,
                   "--gid", 1000, "--full_name", "Another user",
                   "--home_directory", "/tmp"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "UID 2362 is already in use.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddUser)
    unittest.TextTestRunner(verbosity=2).run(suite)
