#!/usr/bin/env python2.6
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand

ARCHETYPE = 'aquilon'


class TestParameterDefinition(TestBrokerCommand):

    def test_100_add(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--template=foo", "--required", "--default=default"]

        self.noouttest(cmd)

    def test_110_add_existing(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--template=foo", "--required", "--default=default"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Parameter Definition testpath, parameter "
                         "definition holder aquilon already exists.",
                         cmd)

    def test_130_add_default_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testdefault", "--description=blaah",
               "--template=foo"]

        self.noouttest(cmd)

    def test_130_add_int_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testint", "--description=blaah",
               "--template=foo", "--value_type=int", "--default=60"]

        self.noouttest(cmd)

    def test_130_add_invalid_int_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadint", "--description=blaah",
               "--template=foo", "--value_type=int", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an integer for default for path=testbadint", cmd)

    def test_130_add_float_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testfloat", "--description=blaah",
               "--template=foo", "--value_type=float", "--default=100.100"]

        self.noouttest(cmd)

    def test_130_add_invalid_float_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadfloat", "--description=blaah",
               "--template=foo", "--value_type=float", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an floating point number for default for path=testbadfloat", cmd)

    def test_130_add_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testboolean", "--description=blaah",
               "--template=foo", "--value_type=boolean", "--default=yes"]

        self.noouttest(cmd)

    def test_130_add_invalid_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadboolean", "--description=blaah",
               "--template=foo", "--value_type=boolean", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected a boolean value for default for path=testbadboolean", cmd)

    def test_130_add_list_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testlist", "--description=blaah",
               "--template=foo", "--value_type=list", "--default=val1,val2"]

        self.noouttest(cmd)

    def test_130_add_json_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testjson", "--description=blaah",
               "--template=foo", "--value_type=json", "--default=\"{'val1':'val2'}\""]

        self.noouttest(cmd)

    def test_130_add_invalid_json_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadjson", "--description=blaah",
               "--template=foo", "--value_type=json", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "The json string specified for default for path=testbadjson is invalid", cmd)

    def test_130_add_noncompileable_arch(self):
        cmd = ["add_parameter_definition", "--archetype", "windows",
               "--path=testint", "--description=blaah",
               "--template=foo", "--value_type=int", "--default=60"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Archetype windows is not compileable.", cmd)

    def test_130_rebuild_required(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=test_rebuild_required", "--description=rebuild_required",
               "--template=foo", "--value_type=string", "--rebuild_required"]

        self.noouttest(cmd)

    def test_140_verify_add(self):
        cmd = ["search_parameter_definition", "--archetype", ARCHETYPE]

        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testpath \[required\]\s*'
                          r'Type: string\s*'
                          r'Template: foo\s*'
                          r'Default: default',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testdefault\s*'
                          r'Type: string\s*'
                          r'Template: foo',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint\s*'
                          r'Type: int\s*'
                          r'Template: foo\s*'
                          r'Default: 60',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testjson\s*'
                          r'Type: json\s*'
                          r'Template: foo\s*'
                          r"Default: \"{'val1':'val2'}\"",
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testlist\s*'
                          r'Type: list\s*'
                          r'Template: foo\s*'
                          r'Default: val1,val2',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testboolean\s*'
                          r'Type: boolean\s*'
                          r'Template: foo\s*'
                          r'Default: yes',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: test_rebuild_required\s*'
                          r'Type: string\s*'
                          r'Template: foo\s*'
                          r'Description: rebuild_required\s*'
                          r'Rebuild Required: True',
                          cmd)

    def test_145_verify_add(self):
        cmd = ["search_parameter_definition", "--archetype", ARCHETYPE, "--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_paramdefinition_msg(out, 8)
        param_defs = p.param_definitions

        self.failUnlessEqual(param_defs[0].path, 'testpath')
        self.failUnlessEqual(param_defs[0].value_type, 'string')
        self.failUnlessEqual(param_defs[0].template, 'foo')
        self.failUnlessEqual(param_defs[0].default, 'default')
        self.failUnlessEqual(param_defs[0].is_required, True)

        self.failUnlessEqual(param_defs[1].path, 'testboolean')
        self.failUnlessEqual(param_defs[1].value_type, 'boolean')
        self.failUnlessEqual(param_defs[1].template, 'foo')
        self.failUnlessEqual(param_defs[1].default, 'yes')

        self.failUnlessEqual(param_defs[2].path, 'testdefault')
        self.failUnlessEqual(param_defs[2].value_type, 'string')
        self.failUnlessEqual(param_defs[2].template, 'foo')
        self.failUnlessEqual(param_defs[2].default, '')

        self.failUnlessEqual(param_defs[3].path, 'testfloat')
        self.failUnlessEqual(param_defs[3].value_type, 'float')
        self.failUnlessEqual(param_defs[3].template, 'foo')
        self.failUnlessEqual(param_defs[3].default, '100.100')

        self.failUnlessEqual(param_defs[4].path, 'testint')
        self.failUnlessEqual(param_defs[4].value_type, 'int')
        self.failUnlessEqual(param_defs[4].template, 'foo')
        self.failUnlessEqual(param_defs[4].default, '60')

        self.failUnlessEqual(param_defs[5].path, 'testjson')
        self.failUnlessEqual(param_defs[5].value_type, 'json')
        self.failUnlessEqual(param_defs[5].template, 'foo')
        self.failUnlessEqual(param_defs[5].default, u'"{\'val1\':\'val2\'}"')

        self.failUnlessEqual(param_defs[6].path, 'testlist')
        self.failUnlessEqual(param_defs[6].value_type, 'list')
        self.failUnlessEqual(param_defs[6].template, 'foo')
        self.failUnlessEqual(param_defs[6].default, "val1,val2")

        self.failUnlessEqual(param_defs[7].path, 'test_rebuild_required')
        self.failUnlessEqual(param_defs[7].value_type, 'string')
        self.failUnlessEqual(param_defs[7].template, 'foo')
        self.failUnlessEqual(param_defs[7].rebuild_required, True)

    def test_150_del_validation(self):
        cmd = ["add_personality", "--archetype", ARCHETYPE,
               "--personality=paramtest", "--eon_id=2", "--host_environment=legacy"]
        self.noouttest(cmd)

        cmd = ["add_parameter", "--personality=paramtest", "--path=testpath",
               "--value=test"]
        self.noouttest(cmd)

        cmd = ["del_parameter_definition", "--archetype", ARCHETYPE, "--path=testpath" ]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path testpath used by following and cannot be deleted", cmd)

        cmd = ["del_parameter", "--personality=paramtest", "--path=testpath"]
        self.noouttest(cmd)

        cmd = ["del_personality", "--archetype", ARCHETYPE, "--personality=paramtest"]
        self.noouttest(cmd)

    def test_200_del(self):
        for path in ['testpath', 'testdefault', 'testint', 'testlist', 'testjson',
                     'testboolean', 'testfloat', 'test_rebuild_required']:
            cmd = ["del_parameter_definition", "--archetype", ARCHETYPE,
                   "--path=%s" % path]
            self.noouttest(cmd)

    def test_200_verify_delete(self):
        cmd = ["search_parameter_definition", "--archetype", ARCHETYPE ]

        err = self.notfoundtest(cmd)
        self.matchoutput(err, "Not Found: No parameter definitions found for archetype aquilon", cmd)

    def test_210_invalid_path_cleaned(self):
        for path in ["/startslash", "endslash/"] :
            cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
                   "--path=%s" % path, "--template=foo", "--value_type=string"]
            self.noouttest(cmd)
        cmd = ["search_parameter_definition", "--archetype", ARCHETYPE]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'Parameter Definition: startslash\s*', cmd)
        self.searchoutput(out, r'Parameter Definition: endslash\s*', cmd)

    def test_215_invalid_path1(self):
        for path in ["!badchar", "@badchar", "#badchar", "$badchar", "%badchar", "^badchar",
                     "&badchar", "*badchar" ":badchar", ";badcharjk", "+badchar"] :
            cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
                   "--path=%s" % path, "--template=foo", "--value_type=string"]
            err = self.badrequesttest(cmd)
            self.matchoutput(err, "Invalid path %s specified, path cannot start with special characters" % path,
                             cmd)

    def test_220_valid_path(self):
        for path in ["multi/part1/part2", "noslash", "valid/with_under", "valid/with.dot",
                     "valid/with-dash", "with_under", "with.dot", "with-dash"] :

            cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
                   "--path=%s" % path, "--template=foo", "--value_type=string"]
            self.noouttest(cmd)

            cmd = ["del_parameter_definition", "--archetype", ARCHETYPE,
                   "--path=%s" % path]
            self.noouttest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterDefinition)
    unittest.TextTestRunner(verbosity=2).run(suite)
