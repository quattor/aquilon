#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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

import json

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand


class TestUpdateParameterDefinition(TestBrokerCommand):

    def test_100_update_arch_paramdef(self):
        cmd = ["update_parameter_definition", "--archetype", "aquilon",
               "--path=foo/testint", "--description=testint", "--required",
               "--activation", "reboot", "--justification", "tcm=12345678"]
        self.statustest(cmd)

    def test_105_verify_update(self):
        cmd = ["show_parameter_definition", "--archetype", "aquilon",
               "--path", "foo/testint"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint \[required\]\s*'
                          r'Type: int\s*'
                          r'Template: foo\s*'
                          r'Activation: reboot\s*'
                          r'Description: testint\s*',
                          cmd)

    def test_110_update_feature_paramdef(self):
        cmd = ["update_parameter_definition", "--feature", "pre_host", "--type=host",
               "--path=testint", "--description=testint",
               "--default=100", "--required", "--justification", "tcm=12345678"]
        self.statustest(cmd)

    def test_115_verify_update_feature(self):
        cmd = ["search_parameter_definition", "--feature", "pre_host", "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint \[required\]\s*'
                          r'Type: int\s*'
                          r'Default: 100\s*'
                          r'Description: testint\s*',
                          cmd)

    def test_130_update_norequired(self):
        cmd = ["update_parameter_definition", "--feature", "pre_host", "--type=host",
               "--path=testint", "--norequired", "--justification", "tcm=12345678"]
        self.noouttest(cmd)

    def test_135_verify_update_feature(self):
        cmd = ["search_parameter_definition", "--feature", "pre_host", "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint\s*'
                          r'Type: int\s*'
                          r'Default: 100\s*'
                          r'Description: testint\s*',
                          cmd)

    def test_200_update_archetype_default(self):
        cmd = ["update_parameter_definition", "--archetype", "aquilon",
               "--path=foo/test_rebuild_required", "--default=default"]
        out = self.unimplementederrortest(cmd)
        self.matchoutput(out, "Archetype-wide parameter definitions cannot "
                         "have default values.",
                         cmd)

    def test_200_update_bad_feature_type(self):
        cmd = ["update_parameter_definition", "--feature", "pre_host",
               "--type=no-such-type", "--path=testpath"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Unknown feature type 'no-such-type'. The valid "
                         "values are: hardware, host, interface.",
                         cmd)

    def test_200_json_schema_update_value_conflict(self):
        new_schema = {
            "schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "key": {
                    "type": "string"
                },
                "values": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                    },
                    "maxItems": 1,
                },
            },
            "additionalProperties": False,
        }

        cmd = ["update_parameter_definition",
               "--feature", "pre_host", "--type", "host",
               "--path", "testjson", "--schema", json.dumps(new_schema)]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "Existing value for personality aquilon/%s "
                         "conflicts with the new schema: [1, 2] is too long" %
                         "inventory",
                         cmd)

    def test_200_json_schema_update_default_conflict(self):
        new_schema = {
            "schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "key": {
                    "type": "string"
                },
            },
            "additionalProperties": False,
        }

        cmd = ["update_parameter_definition",
               "--feature", "pre_host", "--type", "host",
               "--path", "testjson", "--schema", json.dumps(new_schema)]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "The existing default value conflicts with the new schema", cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateParameterDefinition)
    unittest.TextTestRunner(verbosity=2).run(suite)
