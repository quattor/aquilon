#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016  Contributor
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
"""Module for testing parameter support for features."""

import json

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand

SHOW_CMD = ["show", "parameter", "--personality", "inventory"]

ADD_CMD = ["add", "parameter", "--personality", "inventory"]

UPD_CMD = ["update", "parameter", "--personality", "inventory"]

DEL_CMD = ["del", "parameter", "--personality", "inventory"]


class TestParameterFeature(TestBrokerCommand):

    def test_090_verify_feature_proto_noerr(self):
        cmd = ["show", "parameter", "--personality", "utunused/dev", "--format=proto"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out, "Not Found: No parameters found for personality "
                         "aquilon/utunused/dev", cmd)

    # TODO: Move this to test_constraints_parameter
    def test_125_try_del_paramdef(self):
        cmd = ["del_parameter_definition", "--feature", "pre_host", "--type=host",
               "--path=testdefault"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path testdefault used by following and cannot be deleted", cmd)

    def test_400_update_json_schema_value_conflict(self):
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

    def test_400_update_json_schema_default_conflict(self):
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

    def test_600_add_same_name_feature(self):
        feature = "shinynew"
        for type in ["host", "hardware", "interface"]:
            cmd = ["add_parameter_definition", "--feature", feature, "--type", type,
                   "--path", "car", "--value_type", "string"]
            self.noouttest(cmd)

            cmd = ["bind_feature", "--feature", feature, "--personality", "inventory"]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853"])
            self.successtest(cmd)

    def test_610_add_same_name_feature_parameter(self):
        feature = "shinynew"
        path = "car"
        for type in ["host", "hardware", "interface"]:
            cmd = ADD_CMD + ["--path", path, "--value", 'bmw' + type,
                             "--feature", feature, "--type", type]
            self.successtest(cmd)

    def test_620_verify_name_feature_parameter(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Interface Feature: shinynew\s*'
                          r'car: "bmwinterface"', cmd)
        self.searchoutput(out,
                          r'Hardware Feature: shinynew\s*'
                          r'car: "bmwhardware"', cmd)
        self.searchoutput(out,
                          r'Host Feature: shinynew\s*'
                          r'car: "bmwhost"', cmd)

    def test_630_upd_same_name_feature_parameter(self):
        feature = "shinynew"
        path = "car"
        for type in ["host", "hardware", "interface"]:
            cmd = UPD_CMD + ["--path", path, "--value", 'audi' + type,
                             "--feature", feature, "--type", type]
            self.successtest(cmd)

    def test_640_verify_name_feature_parameter(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Interface Feature: shinynew\s*'
                          r'car: "audiinterface"', cmd)
        self.searchoutput(out,
                          r'Hardware Feature: shinynew\s*'
                          r'car: "audihardware"', cmd)
        self.searchoutput(out,
                          r'Host Feature: shinynew\s*'
                          r'car: "audihost"', cmd)

    def test_950_del_same_name_feature_parameter(self):
        feature = "shinynew"
        path = "car"
        for type in ["host", "hardware", "interface"]:
            cmd = DEL_CMD + ["--path", path, "--feature", feature,
                             "--type", type]
            self.noouttest(cmd)

    def test_960_verify_same_name_feature_parameter(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchclean(out, "shinynew", cmd)
        self.searchclean(out, "car", cmd)

    def test_970_unbind_same_name_feature(self):
        feature = "shinynew"
        for type in ["host", "hardware", "interface"]:
            cmd = ["unbind_feature", "--feature", feature, "--personality", "inventory"]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853"])
            self.successtest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
