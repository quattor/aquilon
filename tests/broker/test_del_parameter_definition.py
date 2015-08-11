#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Module for testing parameter definition support."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand

from .test_add_parameter_definition import default_param_defs


class TestDelParameterDefinition(TestBrokerCommand):

    def test_100_del_default(self):
        for path in default_param_defs:
            self.noouttest(["del_parameter_definition", "--archetype", "aquilon",
                            "--path", path])

        for path in ["startslash", "endslash"]:
            self.noouttest(["del_parameter_definition", "--archetype", "aquilon",
                            "--path", path])

    def test_105_verify_delete(self):
        command = ["search_parameter_definition", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Template: foo", command)

    def test_105_verify_plenary_gone(self):
        self.check_plenary_gone("aquilon", "personality", "utpersonality",
                                "foo")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelParameterDefinition)
    unittest.TextTestRunner(verbosity=2).run(suite)
