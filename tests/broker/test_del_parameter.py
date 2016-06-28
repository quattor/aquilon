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
"""Module for testing the del parameter command."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestDelParameter(TestBrokerCommand):

    def test_100_del_testrequired(self):
        self.noouttest(["del_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "foo/testrequired"])

    def test_110_del_single_action(self):
        self.noouttest(["del_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "actions/testaction2"])

        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out, "testaction", command)
        self.matchclean(out, "testaction2", command)

        command = ["cat", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next",
                   "--param_tmpl", "actions"]
        out = self.commandtest(command)
        self.matchoutput(out, "testaction", command)
        self.matchclean(out, "testaction2", command)

    def test_115_del_actions(self):
        self.noouttest(["del_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "actions"])

        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchclean(out, "testaction", command)
        self.matchclean(out, "actions", command)

        command = ["cat", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next",
                   "--param_tmpl", "actions"]
        out = self.commandtest(command)
        self.matchclean(out, "testaction", command)
        self.matchclean(out, "=", command)

    def test_200_del_bad_path(self):
        command = ["del_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--path", "bad-path"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Unknown parameter template bad-path.",
                         command)

    def test_200_del_unknown_path(self):
        command = ["del_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--path", "foo/no-such-path"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Path foo/no-such-path does not match any parameter "
                         "definitions of archetype aquilon.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelParameter)
    unittest.TextTestRunner(verbosity=2).run(suite)
