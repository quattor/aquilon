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

import unittest
from broker.brokertest import TestBrokerCommand


class TestUpdateParameterDefinition(TestBrokerCommand):

    def test_100_update_arch_paramdef_no_justification(self):
        command = ["update_parameter_definition", "--archetype", "aquilon",
                   "--path=foo/testint", "--default=100"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "--justification is required", command)

    def test_101_update_arch_paramdef(self):
        cmd = ["update_parameter_definition", "--archetype", "aquilon",
               "--path=foo/testint", "--description=testint",
               "--default=100", "--required", "--activation", "reboot",
               "--justification", "tcm=12345678"]
        out = self.statustest(cmd)
        self.matchoutput(out, "Flushed", cmd)

    def test_105_verify_update(self):
        cmd = ["show_parameter_definition", "--archetype", "aquilon",
               "--path", "foo/testint"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: foo/testint \[required\]\s*'
                          r'Type: int\s*'
                          r'Template: foo\s*'
                          r'Default: 100\s*'
                          r'Activation: reboot\s*'
                          r'Description: testint\s*',
                          cmd)

    def test_105_cat_unixeng_test(self):
        cmd = ["cat", "--archetype", "aquilon", "--personality", "unixeng-test",
               "--param_tmpl", "foo"]
        out = self.commandtest(cmd)
        self.matchoutput(out, '"testint" = 100;', cmd)

    def test_110_update_feature_paramdef(self):
        cmd = ["update_parameter_definition", "--feature", "myfeature", "--type=host",
               "--path=testint", "--description=testint",
               "--default=100", "--required"]
        self.noouttest(cmd)

    def test_115_verify_update_feature(self):
        cmd = ["search_parameter_definition", "--feature", "myfeature", "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint \[required\]\s*'
                          r'Type: int\s*'
                          r'Default: 100\s*'
                          r'Description: testint\s*',
                          cmd)

    def test_120_clear_default(self):
        command = ["update_parameter_definition", "--archetype", "aquilon",
                   "--path=foo/testint", "--clear_default",
                   "--justification", "tcm=12345678"]
        self.statustest(command)

    def test_125_verify_update(self):
        cmd = ["show_parameter_definition", "--archetype", "aquilon",
               "--path", "foo/testint"]
        out = self.commandtest(cmd)
        self.matchclean(out, "Default:", cmd)

    def test_125_cat_unixeng_test(self):
        cmd = ["cat", "--archetype", "aquilon", "--personality", "unixeng-test",
               "--param_tmpl", "foo"]
        out = self.commandtest(cmd)
        self.matchclean(out, '"testint"', cmd)

    def test_129_restore_default(self):
        command = ["update_parameter_definition", "--archetype", "aquilon",
                   "--path=foo/testint", "--default=100",
                   "--justification", "tcm=12345678"]
        self.statustest(command)

    def test_130_update_norequired(self):
        cmd = ["update_parameter_definition", "--feature", "myfeature", "--type=host",
               "--path=testint", "--norequired"]
        self.noouttest(cmd)

    def test_135_verify_update_feature(self):
        cmd = ["search_parameter_definition", "--feature", "myfeature", "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint\s*'
                          r'Type: int\s*'
                          r'Default: 100\s*'
                          r'Description: testint\s*',
                          cmd)

    def test_200_update_rebuild_required_default(self):
        cmd = ["update_parameter_definition", "--archetype", "aquilon",
               "--path=foo/test_rebuild_required", "--default=default"]
        out = self.unimplementederrortest(cmd)
        self.matchoutput(out, "Changing the default value of a parameter "
                         "which requires rebuild would cause all existing "
                         "hosts to require a rebuild, which is not supported.",
                         cmd)

    def test_200_update_bad_feature_type(self):
        cmd = ["update_parameter_definition", "--feature", "myfeature",
               "--type=no-such-type", "--path=testpath"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Unknown feature type 'no-such-type'. The valid "
                         "values are: hardware, host, interface.",
                         cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateParameterDefinition)
    unittest.TextTestRunner(verbosity=2).run(suite)
