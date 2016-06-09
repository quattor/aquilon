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
import re

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand

test_schema = {
    "schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "key": {
            "type": "string"
        },
        "values": {
            "type": "array",
            "items": {
                "type": "integer"
            },
            "minItems": 1,
            "uniqueItems": True
        }
    },
    "additionalProperties": False
}

default_param_defs = {
    "testdefault": {
        # No explicit type
        "description": "Blah",
    },
    "testrequired": {
        "type": "string",
        "required": True,
    },
    "test_rebuild_required": {
        "type": "string",
        "activation": "rebuild",
    },
    "teststring": {
        "type": "string",
        "default": "default",
    },
    "testint": {
        "type": "int",
        "default": "60",
        "invalid_default": "bad_int",
    },
    "testfloat": {
        "type": "float",
        "default": "100.100",
        "invalid_default": "bad_float",
    },
    "testboolean": {
        "type": "boolean",
        "default": "yes",
        "invalid_default": "bad_boolean",
    },
    "testfalsedefault": {
        "type": "boolean",
        "default": "no",
    },
    "testlist": {
        "type": "list",
        "default": "val1,val2",
    },
    "testjson": {
        "type": "json",
        "default": '{"key": "param_key", "values": [0]}',
        "schema": json.dumps(test_schema),
        "invalid_default": "bad json value",
    },
}

param_features = {
    "host": ["hostfeature"],
    "hardware": ["bios_setup"],
    "interface": ["interfacefeature", "src_route"],
}


class TestAddParameterDefinition(TestBrokerCommand):

    @classmethod
    def setUpClass(cls):
        super(TestAddParameterDefinition, cls).setUpClass()

        cls.proto = cls.protocols['aqdsystems_pb2']
        desc = cls.proto.Feature.DESCRIPTOR
        cls.activation_type = desc.fields_by_name["activation"].enum_type

    def test_100_add_all(self):
        for path, params in default_param_defs.items():
            cmd = ["add_parameter_definition", "--archetype", "aquilon",
                   "--path", "foo/" + path, "--template", "foo"]
            if "type" in params:
                cmd.extend(["--value_type", params["type"]])
            if params.get("required", False):
                cmd.append("--required")
            if "activation" in params:
                cmd.extend(["--activation", params["activation"]])
            if "schema" in params:
                cmd.extend(["--schema", params["schema"]])

            self.noouttest(cmd)

    def test_105_show_paramdef(self):
        cmd = ["show_parameter_definition", "--archetype", "aquilon",
               "--path", "foo/testrequired"]
        out = self.commandtest(cmd)
        self.output_equals(out, """
            Parameter Definition: testrequired [required]
              Type: string
              Template: foo
              Activation: dispatch
            """, cmd)

    def test_120_clean_path(self):
        for path in ["/foo/startslash", "foo/endslash/"]:
            cmd = ["add_parameter_definition", "--archetype", "aquilon",
                   "--path=%s" % path, "--template=foo", "--value_type=string"]
            self.noouttest(cmd)

    def test_130_valid_path(self):
        for path in ["multi/part1/part2", "foo", "valid/with_under", "valid/with.dot",
                     "valid/with-dash", "with_under", "with.dot", "with-dash"]:

            cmd = ["add_parameter_definition", "--archetype", "aquilon",
                   "--path=foo/%s" % path, "--template=foo", "--value_type=string"]
            self.noouttest(cmd)

            cmd = ["del_parameter_definition", "--archetype", "aquilon",
                   "--path=foo/%s" % path]
            self.noouttest(cmd)

    def load_feature_paramdefs(self, feature, feature_type):
        for path, params in default_param_defs.items():
            # Activation cannot be set for feature parameters
            if "activation" in params:
                continue

            cmd = ["add_parameter_definition", "--feature", feature,
                   "--type", feature_type, "--path", path]
            if "type" in params:
                cmd.extend(["--value_type", params["type"]])
            if "default" in params:
                cmd.extend(["--default", params["default"]])
            if params.get("required", False):
                cmd.append("--required")
            if "schema" in params:
                cmd.extend(["--schema", params["schema"]])

            self.noouttest(cmd)

    def test_200_add_feature_all(self):
        for feature_type, features in param_features.items():
            for feature in features:
                self.load_feature_paramdefs(feature, feature_type)

    def test_205_show_testrequired(self):
        cmd = ["show_parameter_definition", "--feature", "hostfeature", "--type=host",
               "--path=testrequired"]
        out = self.commandtest(cmd)
        self.output_equals(out, """
            Parameter Definition: testrequired [required]
              Type: string
            """, cmd)

    def test_220_clean_path(self):
        for path in ["/startslash", "endslash/"]:
            cmd = ["add_parameter_definition", "--feature", "hostfeature", "--type=host",
                   "--path=%s" % path, "--value_type=string"]
            self.noouttest(cmd)
        cmd = ["search_parameter_definition", "--feature", "hostfeature", "--type=host"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'Parameter Definition: startslash\s*', cmd)
        self.searchoutput(out, r'Parameter Definition: endslash\s*', cmd)

    def test_230_valid_path(self):
        for path in ["multi/part1/part2", "noslash", "valid/with_under", "valid/with.dot",
                     "valid/with-dash", "with_under", "with.dot", "with-dash"]:

            cmd = ["add_parameter_definition", "--path=%s" % path,
                   "--feature", "hostfeature", "--type=host", "--value_type=string"]
            self.noouttest(cmd)

            cmd = ["del_parameter_definition", "--feature", "hostfeature", "--type=host",
                   "--path=%s" % path]
            self.noouttest(cmd)

    def test_300_add_existing(self):
        cmd = ["add_parameter_definition", "--archetype", "aquilon",
               "--path=foo/teststring", "--value_type=string", "--description=blaah",
               "--template=foo", "--required"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "The path cannot be a strict subset or superset "
                         "of an existing definition.",
                         cmd)

    def test_300_path_conflict_sub(self):
        cmd = ["add_parameter_definition", "--archetype", "aquilon",
               "--path", "foo/testjson/subpath", "--template", "foo",
               "--value_type", "list"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "The path cannot be a strict subset or superset "
                         "of an existing definition.",
                         cmd)

    def test_300_path_conflict_super(self):
        cmd = ["add_parameter_definition", "--archetype", "aquilon",
               "--path", "foo", "--template", "foo",
               "--value_type", "json"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "The path cannot be a strict subset or superset "
                         "of an existing definition.",
                         cmd)

    def test_300_add_feature_existing(self):
        cmd = ["add_parameter_definition", "--feature", "hostfeature", "--type=host",
               "--path=teststring", "--value_type=string", "--description=blaah",
               "--required"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "The path cannot be a strict subset or superset "
                         "of an existing definition.",
                         cmd)

    def test_300_path_conflict_feature(self):
        cmd = ["add_parameter_definition",
               "--feature", "hostfeature", "--type=host",
               "--path=testjson/subpath", "--value_type=string"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "The path cannot be a strict subset or superset "
                         "of an existing definition.",
                         cmd)

    def test_300_invalid_feature_defaults(self):
        for path, params in default_param_defs.items():
            if "invalid_default" not in params:
                continue

            cmd = ["add_parameter_definition", "--feature", "hostfeature", "--type", "host",
                   "--path", path + "_invalid_default",
                   "--value_type", params["type"],
                   "--default", params["invalid_default"]]
            out = self.badrequesttest(cmd)
            self.matchoutput(out, "for default for path=%s" % path, cmd)

    def test_300_add_noncompileable_arch(self):
        cmd = ["add_parameter_definition", "--archetype", "windows",
               "--path=foo/testint", "--description=blaah",
               "--template=foo", "--value_type=int"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Archetype windows is not compileable.", cmd)

    def test_300_add_archetype_default(self):
        cmd = ["add_parameter_definition", "--archetype", "aquilon",
               "--path=foo/test_arch_default", "--default=default",
               "--template=foo", "--value_type=string"]
        out = self.unimplementederrortest(cmd)
        self.matchoutput(out,
                         "Archetype-wide parameter definitions cannot have "
                         "default values.",
                         cmd)

    def test_300_invalid_path(self):
        for path in ["!badchar", "@badchar", "#badchar", "$badchar", "%badchar", "^badchar",
                     "&badchar", "*badchar" ":badchar", ";badcharjk", "+badchar"]:
            cmd = ["add_parameter_definition", "--archetype", "aquilon",
                   "--path=foo/%s" % path, "--template=foo", "--value_type=string"]
            err = self.badrequesttest(cmd)
            self.matchoutput(err,
                             "'%s' is not a valid value for a path component." % path,
                             cmd)

    def test_300_wrong_toplevel_type(self):
        cmd = ["add_parameter_definition", "--archetype", "aquilon",
               "--path", "bad_toplevel_type", "--template", "bad_toplevel_type",
               "--value_type", "list"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "Only the JSON type can be used for top-level "
                         "parameter definitions.",
                         cmd)

    def test_300_show_bad_path(self):
        cmd = ["show_parameter_definition", "--archetype", "aquilon",
               "--path", "foo/path-does-not-exist"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out,
                         "Path foo/path-does-not-exist does not match any "
                         "parameter definitions of archetype aquilon.",
                         cmd)

    def test_300_show_archetype_no_params(self):
        cmd = ["show_parameter_definition", "--archetype", "windows",
               "--path", "path-does-not-exist"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "Unknown parameter template path-does-not-exist.",
                         cmd)

    def test_300_invalid_path_feature(self):
        for path in ["!badchar", "@badchar", "#badchar", "$badchar", "%badchar", "^badchar",
                     "&badchar", "*badchar", ":badchar", ";badcharjk", "+badchar"]:
            cmd = ["add_parameter_definition", "--feature", "hostfeature", "--type=host",
                   "--path=%s" % path, "--value_type=string"]
            err = self.badrequesttest(cmd)
            self.matchoutput(err,
                             "'%s' is not a valid value for a path component." % path,
                             cmd)

    def test_300_add_bad_feature_type(self):
        cmd = ["add_parameter_definition", "--feature", "hostfeature",
               "--type=no-such-type",
               "--path=testpath", "--value_type=string"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Unknown feature type 'no-such-type'. The valid "
                         "values are: hardware, host, interface.",
                         cmd)

    def test_300_search_bad_feature_type(self):
        cmd = ["search_parameter_definition", "--feature", "hostfeature",
               "--type=no-such-type"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Unknown feature type 'no-such-type'. The valid "
                         "values are: hardware, host, interface.",
                         cmd)

    def test_300_show_bad_path_feature(self):
        cmd = ["show_parameter_definition", "--feature", "hostfeature",
               "--type", "host", "--path", "path-does-not-exist"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out,
                         "Path path-does-not-exist does not match any "
                         "parameter definitions of host feature hostfeature.",
                         cmd)

    def test_300_show_feature_no_params(self):
        cmd = ["show_parameter_definition", "--feature", "unused_no_params",
               "--type", "host", "--path", "path-does-not-exist"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out,
                         "No parameter definitions found for host feature "
                         "unused_no_params.",
                         cmd)

    def test_400_verify_all(self):
        cmd = ["search_parameter_definition", "--archetype", "aquilon"]

        out = self.commandtest(cmd)
        for path, params in default_param_defs.items():
            pattern = "Parameter Definition: " + path
            if params.get("required", False):
                pattern += r' \[required\]'
            pattern += r"\s*"
            if "type" in params:
                pattern += "Type: " + params["type"] + r"\s*"
                if params["type"] == "json" and "schema" in params:
                    pattern += r"Schema: \{\n(^            .*\n)+\s*\}\s*"
            else:
                pattern += r"Type: string\s*"
            pattern += r"Template: foo\s*"
            if "activation" in params:
                pattern += "Activation: " + params["activation"] + r"\s*"
            else:
                pattern += r"Activation: dispatch\s*"

            self.searchoutput(out, pattern, cmd)

        self.searchoutput(out, r'Parameter Definition: startslash\s*', cmd)
        self.searchoutput(out, r'Parameter Definition: endslash\s*', cmd)

    def test_400_verify_all_proto(self):
        cmd = ["search_parameter_definition", "--archetype", "aquilon", "--format=proto"]
        result = self.protobuftest(cmd, expect=12)[:]
        param_defs = {param_def.path: param_def for param_def in result}

        self.assertIn('foo/endslash', param_defs)
        self.assertEqual(param_defs['foo/endslash'].value_type, 'string')
        self.assertIn('foo/startslash', param_defs)
        self.assertEqual(param_defs['foo/startslash'].value_type, 'string')

        for path, params in default_param_defs.items():
            self.assertIn("foo/" + path, param_defs)
            paramdef = param_defs["foo/" + path]

            self.assertEqual(paramdef.template, "foo")
            if "type" in params:
                self.assertEqual(paramdef.value_type, params["type"])
            else:
                self.assertEqual(paramdef.value_type, "string")
            self.assertEqual(paramdef.default, "")
            self.assertEqual(paramdef.is_required,
                             params.get("required", False))
            if "activation" in params:
                val = self.activation_type.values_by_name[params["activation"].upper()]
                self.assertEqual(paramdef.activation, val.number)
            else:
                self.assertEqual(paramdef.activation, self.proto.DISPATCH)

    def test_410_verify_feature_all(self):
        cmd = ["search_parameter_definition", "--feature", "hostfeature", "--type=host"]
        out = self.commandtest(cmd)

        for path, params in default_param_defs.items():
            if "activation" in params:
                continue

            pattern = "Parameter Definition: " + path
            if params.get("required", False):
                pattern += r' \[required\]'
            pattern += r"\s*"
            if "type" in params:
                pattern += "Type: " + params["type"] + r"\s*"
                if params["type"] == "json" and "schema" in params:
                    pattern += r"Schema: \{\n(^            .*\n)+\s*\}\s*"
            else:
                pattern += r"Type: string\s*"
            if "default" in params:
                pattern += "Default: " + re.escape(params["default"]) + r"\s*"

            self.searchoutput(out, pattern, cmd)

        self.matchclean(out, "Activation", cmd)

    def test_410_verify_feature_all_proto(self):
        cmd = ["search_parameter_definition", "--feature", "hostfeature", "--format=proto", "--type=host"]
        result = self.protobuftest(cmd, expect=11)[:]
        param_defs = {param_def.path: param_def for param_def in result}

        for path, params in default_param_defs.items():
            if "activation" in params:
                continue

            self.assertIn(path, param_defs)
            self.assertEqual(param_defs[path].template, "")
            if "type" in params:
                self.assertEqual(param_defs[path].value_type, params["type"])
            else:
                self.assertEqual(param_defs[path].value_type, "string")
            if "default" in params:
                self.assertEqual(param_defs[path].default, params["default"])
            else:
                self.assertEqual(param_defs[path].default, "")
            self.assertEqual(param_defs[path].is_required,
                             params.get("required", False))
            #self.assertEqual(param_defs[path].activation, self.proto.NONE)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddParameterDefinition)
    unittest.TextTestRunner(verbosity=2).run(suite)
