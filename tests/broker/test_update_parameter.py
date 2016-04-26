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
"""Module for testing the update parameter command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand


class TestUpdateParameter(TestBrokerCommand):

    def check_match(self, out, expected, command):
        out = ' '.join(out.split())
        self.matchoutput(out, expected, command)

    def test_100_update_existing_leaf_path(self):
        self.noouttest(["update_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "actions/testaction/user",
                        "--value", "user2"])

        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        expected = 'testaction: { "command": "/bin/testaction", "user": "user2" }'
        self.check_match(out, expected, command)

    def test_110_upd_existing_path(self):
        self.noouttest(["update_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "espinfo/function", "--value", "production"])

    def test_200_upd_nonexisting_leaf_path(self):
        command = ["update_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "actions/testaction/badpath", "--value", "badvalue"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "No parameter of path=testaction/badpath defined.",
                         command)

    def test_200_upd_nonexisting_path(self):
        command = ["update_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "espinfo/badpath", "--value", "badvalue"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Path espinfo/badpath does not match any parameter "
                         "definitions of archetype aquilon.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateParameter)
    unittest.TextTestRunner(verbosity=2).run(suite)
