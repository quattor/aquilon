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

    def test_200_refresh(self):
        command = ["refresh", "user"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Added 2, deleted 1, update 1 Users.", command)

    def test_210_verifyuser(self):
        command = ["show_user", "--all"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "testuser1", command)
        self.matchoutput(out, "testuser2", command)
        self.matchoutput(out, "test user 3", command)

    def test_220_verifyuser(self):
        command = ["show_user", "--username", "testuser1"]
        (out, err) = self.successtest(command)
        self.searchoutput(out, r'User: testuser1', command)
        self.searchoutput(out, r'Uid: 1234', command)
        self.searchoutput(out, r'Gid: 423', command)
        self.searchoutput(out, r'Full Name: test user 1', command)
        self.searchoutput(out, r'Home Dir: \/tmp', command)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshUser)
    unittest.TextTestRunner(verbosity=2).run(suite)
