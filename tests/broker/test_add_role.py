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
"""Module for testing the add_role command.
"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRole(TestBrokerCommand):
    def test_100_add_engineering(self):
        self.noouttest(["add_role", "--role", "engineering"])

    def test_105_show_engineering(self):
        command = ["show_role", "--role", "engineering"]
        out = self.commandtest(command)
        self.matchoutput(out, "Role: engineering", command)

    def test_110_add_operations(self):
        self.noouttest(["add_role", "--role", "operations"])

    def test_200_add_engineering_again(self):
        command = ["add_role", "--role", "engineering"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Role engineering already exists.", command)

    def test_300_show_all(self):
        command = ["show_role", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Role: engineering", command)
        self.matchoutput(out, "Role: operations", command)
        self.matchoutput(out, "Role: nobody", command)
        self.matchoutput(out, "Role: aqd_admin", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRole)
    unittest.TextTestRunner(verbosity=2).run(suite)
