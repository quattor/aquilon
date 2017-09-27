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
"""Module for testing the del_role command.
"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelRole(TestBrokerCommand):
    def test_100_del_engineering_inuse(self):
        command = ["del_role", "--role", "engineering"]
        self.badrequesttest(command)

    def test_101_demote_user(self):
        self.noouttest(["permission", "--principal", "testuserengineering@" + self.realm,
                        "--role", "nobody"] + self.valid_just_sn)
        self.noouttest(["permission", "--principal", "testuserpromote@" + self.realm,
                        "--role", "nobody"] + self.valid_just_sn)

    def test_102_del_engineering(self):
        self.noouttest(["del_role", "--role", "engineering"])

    def test_105_show_engineering(self):
        command = ["show_role", "--role", "engineering"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Role engineering not found.", command)

    def test_200_del_aqd_eng(self):
        # The current user has this role
        command = ["del_role", "--role", "aqd_admin"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Role aqd_admin is still in use, and cannot be deleted.", command)

    def test_300_show_all(self):
        command = ["show_role", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Role: nobody", command)
        self.matchoutput(out, "Role: aqd_admin", command)
        self.matchclean(out, "engineering", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRole)
    unittest.TextTestRunner(verbosity=2).run(suite)
