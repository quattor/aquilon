#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Module for testing parameter support."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand

FEATURE = 'myfeature'


class TestParameterDefinitionFeature(TestBrokerCommand):

    def test_00_add_feature(self):
        cmd = ["add_feature", "--feature", FEATURE, "--type=host"]
        self.noouttest(cmd)

    def test_100_add(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--required", "--default=default"]

        self.noouttest(cmd)

    def test_110_add_existing(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--required", "--default=default"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Parameter Definition testpath, parameter "
                         "definition holder myfeature already exists.",
                         cmd)

    def test_130_add_default_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testdefault", "--description=blaah"]

        self.noouttest(cmd)

    def test_130_add_int_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testint", "--description=blaah",
               "--value_type=int", "--default=60"]

        self.noouttest(cmd)

    def test_130_add_invalid_int_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testbadint", "--description=blaah",
               "--value_type=int", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an integer for default for path=testbadint", cmd)

    def test_130_add_float_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testfloat", "--description=blaah",
               "--value_type=float", "--default=100.100"]

        self.noouttest(cmd)

    def test_130_add_invalid_float_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testbadfloat", "--description=blaah",
               "--value_type=float", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an floating point number for default for path=testbadfloat", cmd)

    def test_130_add_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testboolean", "--description=blaah",
               "--value_type=boolean", "--default=yes"]

        self.noouttest(cmd)

    def test_130_add_invalid_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testbadboolean", "--description=blaah",
               "--value_type=boolean", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected a boolean value for default for path=testbadboolean", cmd)

    def test_130_add_list_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testlist", "--description=blaah",
               "--value_type=list", "--default=val1,val2"]

        self.noouttest(cmd)

    def test_130_add_json_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testjson", "--description=blaah",
               "--value_type=json", "--default=\"{'val1':'val2'}\""]

        self.noouttest(cmd)

    def test_130_add_invalid_json_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testbadjson", "--description=blaah",
               "--value_type=json", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "The json string specified for default for path=testbadjson is invalid", cmd)

    def test_130_rebuild_required(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=test_rebuild_required", "--value_type=string", "--rebuild_required"]

        self.noouttest(cmd)

    def test_140_verify_add(self):
        cmd = ["search_parameter_definition", "--feature", FEATURE, "--type=host"]

        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testpath \[required\]\s*'
                          r'Type: string\s*'
                          r'Default: default',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testdefault\s*'
                          r'Type: string',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint\s*'
                          r'Type: int\s*'
                          r'Default: 60',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testjson\s*'
                          r'Type: json\s*'
                          r"Default: \"{'val1':'val2'}\"",
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testlist\s*'
                          r'Type: list\s*'
                          r'Default: val1,val2',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: test_rebuild_required\s*'
                          r'Type: string\s*'
                          r'Rebuild Required: True',
                          cmd)

    def test_145_verify_add(self):
        cmd = ["search_parameter_definition", "--feature", FEATURE, "--format=proto", "--type=host"]
        out = self.commandtest(cmd)
        p = self.parse_paramdefinition_msg(out, 8)
        param_defs = p.param_definitions[:]
        param_defs.sort(key=lambda x: x.path)

        self.failUnlessEqual(param_defs[0].path, 'test_rebuild_required')
        self.failUnlessEqual(param_defs[0].value_type, 'string')
        self.failUnlessEqual(param_defs[0].rebuild_required, True)

        self.failUnlessEqual(param_defs[1].path, 'testboolean')
        self.failUnlessEqual(param_defs[1].value_type, 'boolean')
        self.failUnlessEqual(param_defs[1].default, 'yes')

        self.failUnlessEqual(param_defs[2].path, 'testdefault')
        self.failUnlessEqual(param_defs[2].value_type, 'string')
        self.failUnlessEqual(param_defs[2].default, '')

        self.failUnlessEqual(param_defs[3].path, 'testfloat')
        self.failUnlessEqual(param_defs[3].value_type, 'float')
        self.failUnlessEqual(param_defs[3].default, '100.100')

        self.failUnlessEqual(param_defs[4].path, 'testint')
        self.failUnlessEqual(param_defs[4].value_type, 'int')
        self.failUnlessEqual(param_defs[4].default, '60')

        self.failUnlessEqual(param_defs[5].path, 'testjson')
        self.failUnlessEqual(param_defs[5].value_type, 'json')
        self.failUnlessEqual(param_defs[5].default, u'"{\'val1\':\'val2\'}"')

        self.failUnlessEqual(param_defs[6].path, 'testlist')
        self.failUnlessEqual(param_defs[6].value_type, 'list')
        self.failUnlessEqual(param_defs[6].default, "val1,val2")

        self.failUnlessEqual(param_defs[7].path, 'testpath')
        self.failUnlessEqual(param_defs[7].value_type, 'string')
        self.failUnlessEqual(param_defs[7].default, 'default')
        self.failUnlessEqual(param_defs[7].is_required, True)

    def test_146_update(self):
        cmd = ["update_parameter_definition", "--feature", FEATURE, "--type=host",
              "--path=testint", "--description=testint",
              "--default=100", "--required",
              "--rebuild_required"]
        self.noouttest(cmd)

    def test_147_verify_add(self):
        cmd = ["search_parameter_definition", "--feature", FEATURE, "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint \[required\]\s*'
                          r'Type: int\s*'
                          r'Default: 100\s*'
                          r'Description: testint\s*'
                          r'Rebuild Required: True',
                          cmd)

    def test_150_del_validation(self):
        cmd = ["add_personality", "--archetype=aquilon", "--personality=paramtest", "--eon_id=2", "--host_environment=dev"]
        self.noouttest(cmd)

        cmd = ["bind_feature", "--personality=paramtest", "--feature", FEATURE]
        self.successtest(cmd)

        cmd = ["add_parameter", "--personality=paramtest", "--feature", FEATURE,
               "--path=testpath", "--value=hello"]
        self.noouttest(cmd)

        cmd = ["del_parameter_definition", "--feature", FEATURE, "--type=host",
               "--path=testpath"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path testpath used by following and cannot be deleted", cmd)

        cmd = ["del_parameter", "--personality=paramtest", "--feature", FEATURE, "--path=testpath"]
        self.noouttest(cmd)

        cmd = ["unbind_feature", "--personality=paramtest", "--feature", FEATURE]
        self.successtest(cmd)

        cmd = ["del_personality", "--archetype=aquilon", "--personality=paramtest"]
        self.noouttest(cmd)

    def test_200_del(self):
        for path in ['testpath', 'testdefault', 'testint', 'testlist',
                     'testjson', 'testboolean', 'testfloat', 'test_rebuild_required']:
            cmd = ["del_parameter_definition", "--feature", FEATURE,
                   "--type=host", "--path=%s" % path]
            self.noouttest(cmd)

    def test_200_verify_delete(self):
        cmd = ["search_parameter_definition", "--feature", FEATURE, "--type=host" ]

        err = self.notfoundtest(cmd)
        self.matchoutput(err, "No parameter definitions found for host "
                         "feature myfeature", cmd)

    def test_210_invalid_path_cleaned(self):
        for path in ["/startslash", "endslash/"] :
            cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
                   "--path=%s" % path,  "--value_type=string"]
            self.noouttest(cmd)
        cmd = ["search_parameter_definition", "--feature", FEATURE, "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'Parameter Definition: startslash\s*', cmd)
        self.searchoutput(out, r'Parameter Definition: endslash\s*', cmd)

    def test_215_invalid_path1(self):
        for path in ["!badchar", "@badchar", "#badchar", "$badchar", "%badchar", "^badchar",
                     "&badchar", "*badchar" ":badchar", ";badcharjk", "+badchar"] :
            cmd = ["add_parameter_definition", "--feature", FEATURE, "--type=host",
                   "--path=%s" % path, "--value_type=string"]
            err = self.badrequesttest(cmd)
            self.matchoutput(err, "Invalid path %s specified, path cannot start with special characters" % path,
                             cmd)

    def test_220_valid_path(self):
        for path in ["multi/part1/part2", "noslash", "valid/with_under", "valid/with.dot",
                     "valid/with-dash", "with_under", "with.dot", "with-dash"] :

            cmd = ["add_parameter_definition", "--path=%s" % path,
                   "--feature", FEATURE, "--type=host", "--value_type=string"]
            self.noouttest(cmd)

            cmd = ["del_parameter_definition", "--feature", FEATURE, "--type=host",
                   "--path=%s" % path]
            self.noouttest(cmd)

    def test_300_del(self):
        cmd = ["del_feature", "--feature", FEATURE, "--type=host" ]
        self.noouttest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterDefinitionFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
