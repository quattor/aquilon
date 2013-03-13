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
"""Module for testing parameter support for features."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand

PERSONALITY = 'unixeng-test'
ARCHETYPE = 'aquilon'
HOSTFEATURE = 'hostfeature'
HARDWAREFEATURE = 'hardwarefeature'
INTERFACEFEATURE = 'interfacefeature'
OTHER_PERSONALITY = 'eaitools'

## validation parameters by templates
PARAM_DEFS = [
    {"path": "teststring", "value_type": "string", "description": "test string"},
    {"path": "testlist", "value_type": "list", "description": "test list"},
    {"path": "testrequired", "value_type": "string", "description": "test required", "required": "true"},
    {"path": "testdefault", "value_type": "string", "description": "test required", "default": "defaultval"},
]

SHOW_CMD = ["show", "parameter"]

ADD_CMD = ["add", "parameter"]

UPD_CMD = ["update", "parameter"]

DEL_CMD = ["del", "parameter"]

CAT_CMD = ["cat", "--personality", PERSONALITY]

VAL_CMD = ["validate_parameter"]


class TestParameterFeature(TestBrokerCommand):

    def test_000_add_host_feature(self):
        type = "host"
        cmd = ["add_feature", "--feature", HOSTFEATURE, "--type", type, "--post_personality"]
        self.ignoreoutputtest(cmd)

    def test_010_bind_host_feature(self):
        cmd = ["bind_feature", "--feature", HOSTFEATURE,
               "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

    def test_020_verify_host_feature(self):
        type = "host"
        cmd = SHOW_CMD + ["--feature", HOSTFEATURE, "--type", type,
                          "--personality", PERSONALITY]
        err = self.notfoundtest(cmd)
        self.matchoutput(err, "No parameters found for feature %s." % HOSTFEATURE, cmd)
        self.load_paramdefs(HOSTFEATURE, type)

    def test_030_add_hardware_feature(self):
        type = "hardware"
        cmd = ["add_feature", "--feature", HARDWAREFEATURE, "--type", type]
        self.ignoreoutputtest(cmd)

    def test_040_bind_hardware_feature(self):
        cmd = ["bind_feature", "--feature", HARDWAREFEATURE,
               "--archetype", ARCHETYPE, "--justification=tcm=12345678", "--model", "hs21-8853l5u"]
        self.ignoreoutputtest(cmd)

    def test_050_verify_hardware_feature(self):
        type = "hardware"
        cmd = SHOW_CMD + ["--feature", HARDWAREFEATURE, "--type", type,
                          "--archetype", ARCHETYPE]
        err = self.notfoundtest(cmd)
        self.matchoutput(err, "No parameters found for feature %s." % HARDWAREFEATURE, cmd)
        self.load_paramdefs(HARDWAREFEATURE, type)

    def test_060_add_interface_feature(self):
        type = "interface"
        cmd = ["add_feature", "--feature", INTERFACEFEATURE, "--type", type]
        self.ignoreoutputtest(cmd)

    def test_070_bind_interface_feature(self):
        cmd = ["bind_feature", "--feature", INTERFACEFEATURE,
               "--personality", PERSONALITY, "--interface", "eth0"]
        self.ignoreoutputtest(cmd)

    def test_080_verify_interface_feature(self):
        type = "interface"
        cmd = SHOW_CMD + ["--feature", INTERFACEFEATURE, "--type", type,
                          "--personality", PERSONALITY]
        err = self.notfoundtest(cmd)
        self.matchoutput(err, "No parameters found for feature %s." % INTERFACEFEATURE, cmd)
        self.load_paramdefs(INTERFACEFEATURE, type)

    def load_paramdefs(self, feature, feature_type):
        for p in PARAM_DEFS:
            cmd = ["add_parameter_definition", "--feature", feature,
                   "--type", feature_type, "--path", p["path"],
                       "--value_type", p["value_type"]]
            if "required" in p:
                cmd.append("--required")
            if "default" in p:
                cmd.extend(["--default", p["default"]])

            self.noouttest(cmd)

    def test_100_add_path_host_feature(self):
        path = "teststring"
        value = "host_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", HOSTFEATURE, "--personality", PERSONALITY]
        self.noouttest(cmd)

        path = "testlist"
        value = "host1,host2"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", HOSTFEATURE, "--personality", PERSONALITY]
        self.noouttest(cmd)

    def test_110_verify_host_feature(self):
        type = "host"
        cmd = SHOW_CMD + ["--feature", HOSTFEATURE, "--type", type,
                          "--personality", PERSONALITY]
        out = self.commandtest(cmd)
        self.matchoutput(out, 'teststring: "host_feature"', cmd)
        self.matchoutput(out, 'testlist: "host1,host2"', cmd)

    def test_110_verify_host_feature_proto(self):
        type = "host"
        cmd = SHOW_CMD + ["--feature", HOSTFEATURE, "--type", type,
                          "--personality", PERSONALITY, "--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 2)
        params = p.parameters

        self.failUnlessEqual(params[0].path, 'teststring')
        self.failUnlessEqual(params[0].value, 'host_feature')
        self.failUnlessEqual(params[1].path, 'testlist')
        self.failUnlessEqual(params[1].value, 'host1,host2')

    def test_120_verify_cat_host_feature(self):
        cmd = CAT_CMD + ["--personality", PERSONALITY, "--post_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'variable testdefault = "defaultval";\s*'
                               r'variable testlist = list\(\s*'
                               r'"host1",\s*"host2"\s*\);\s*'
                               r'variable teststring = "host_feature";\s*'
                               r'include \{ "features/hostfeature/config" \};',
                          cmd)

    def test_130_validate(self):
        cmd = VAL_CMD + ["--feature", HOSTFEATURE, "--personality", PERSONALITY]

        out = self.badrequesttest(cmd)

        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string',
                          cmd)

    def test_200_add_path_interface_feature(self):
        path = "teststring"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", INTERFACEFEATURE, "--personality", PERSONALITY]
        self.noouttest(cmd)

        path = "testlist"
        value = "intf1,intf2"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", INTERFACEFEATURE, "--personality", PERSONALITY]
        self.noouttest(cmd)

    def test_210_verify_interface_feature(self):
        type = "interface"
        cmd = SHOW_CMD + ["--feature", INTERFACEFEATURE, "--type", type,
                          "--personality", PERSONALITY]
        out = self.commandtest(cmd)
        self.matchoutput(out, 'teststring: "interface_feature"', cmd)
        self.matchoutput(out, 'testlist: "intf1,intf2"', cmd)

    def test_210_verify_host_feature_proto(self):
        type = "interface"
        cmd = SHOW_CMD + ["--feature", INTERFACEFEATURE, "--type", type,
                          "--personality", PERSONALITY, "--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 2)
        params = p.parameters

        self.failUnlessEqual(params[0].path, 'teststring')
        self.failUnlessEqual(params[0].value, 'interface_feature')
        self.failUnlessEqual(params[1].path, 'testlist')
        self.failUnlessEqual(params[1].value, 'intf1,intf2')

    def test_220_verify_cat_interface_feature(self):
        cmd = CAT_CMD + ["--personality", PERSONALITY, "--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'variable testdefault = "defaultval";\s*'
                               r'variable testlist = list\(\s*'
                               r'"intf1",\s*"intf2"\s*\);\s*'
                               r'variable teststring = "interface_feature";\s*'
                               r'variable CURRENT_INTERFACE = "eth0";\s*'
                               r'include \{ "features/interface/interfacefeature/config" \};',
                         cmd)

    def test_230_validate(self):
        cmd = VAL_CMD + ["--feature", INTERFACEFEATURE, "--personality", PERSONALITY]

        out = self.badrequesttest(cmd)

        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string',
                          cmd)

    def test_240_validate_argerror(self):
        cmd = VAL_CMD + ["--feature", INTERFACEFEATURE]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Validating parameter on feature binding needs personality or archetype", cmd)

    def test_250_add_argerror(self):
        path = "teststring"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", INTERFACEFEATURE]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Adding parameter on feature binding needs personality or archetype", cmd)

    def test_260_add_existing(self):
        path = "teststring"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", INTERFACEFEATURE, "--personality", PERSONALITY]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path=teststring already exists", cmd)

    def test_300_add_path_hardware_feature(self):
        path = "teststring"
        value = "hardware_feature"
        feature = "hardwarefeature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", feature, "--archetype", ARCHETYPE]
        self.noouttest(cmd)

        path = "testlist"
        value = "hardware1,hardware2"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", feature, "--archetype", ARCHETYPE]
        self.noouttest(cmd)

    def test_310_verify_hardware_feature(self):
        cmd = SHOW_CMD + ["--feature", HARDWAREFEATURE, "--type=hardware",
                          "--archetype", ARCHETYPE]
        out = self.commandtest(cmd)
        self.matchoutput(out, 'teststring: "hardware_feature"', cmd)
        self.matchoutput(out, 'testlist: "hardware1,hardware2"', cmd)

    def test_310_verify_host_feature_proto(self):
        cmd = SHOW_CMD + ["--feature", HARDWAREFEATURE, "--type=hardware",
                          "--archetype", ARCHETYPE, "--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 2)
        params = p.parameters

        self.failUnlessEqual(params[0].path, 'teststring')
        self.failUnlessEqual(params[0].value, 'hardware_feature')
        self.failUnlessEqual(params[1].path, 'testlist')
        self.failUnlessEqual(params[1].value, 'hardware1,hardware2')

    def test_320_verify_cat_hardware_feature(self):
        cmd = CAT_CMD + ["--personality", PERSONALITY, "--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'variable testdefault = "defaultval";\s*'
                               r'variable testlist = list\(\s*'
                               r'"hardware1",\s*"hardware2"\s*\);\s*'
                               r'variable teststring = "hardware_feature";\s*',
                          cmd)
        self.searchoutput(out, r'include \{\s*'
                               r'if \(\(value\("/hardware/manufacturer"\) == "ibm"\) &&\s*'
                               r'\(value\("/hardware/template_name"\) == "hs21-8853l5u"\)\)\{\s*'
                               r'return\("features/hardware/hardwarefeature"\)\s*'
                               r'\} else\{ return\(undef\); \};\s*};',
                          cmd)

    def test_330_validate(self):
        cmd = VAL_CMD + ["--feature", HARDWAREFEATURE, "--archetype", ARCHETYPE]

        out = self.badrequesttest(cmd)

        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string',
                          cmd)

    def test_340_validate_argerror(self):
        cmd = VAL_CMD + ["--feature", HARDWAREFEATURE]

        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Validating parameter on feature binding needs personality or archetype", cmd)

    def test_350_add_argerror(self):
        path = "teststring"
        value = "hardware_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--archetype", ARCHETYPE]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameters can be added for personality or feature", cmd)

    def test_360_add_existing(self):
        path = "teststring"
        value = "hardware_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", HARDWAREFEATURE, "--archetype", ARCHETYPE]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path=teststring already exists", cmd)

    def test_370_upd_existing(self):
        path = "teststring"
        value = "hardware_newstring"
        cmd = UPD_CMD + ["--path", path, "--value", value,
                         "--feature", HARDWAREFEATURE, "--archetype", ARCHETYPE]
        out = self.noouttest(cmd)

    def test_380_verify_hardware_feature(self):
        type = "hardware"
        cmd = SHOW_CMD + ["--feature", HARDWAREFEATURE, "--type", type,
                          "--archetype", ARCHETYPE]
        out = self.commandtest(cmd)
        self.matchoutput(out, 'teststring: "hardware_newstring"', cmd)
        self.matchoutput(out, 'testlist: "hardware1,hardware2"', cmd)

    def test_390_verify_cat_hardware_feature(self):
        cmd = CAT_CMD + ["--personality", PERSONALITY, "--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'variable testdefault = "defaultval";\s*'
                               r'variable testlist = list\(\s*'
                               r'"hardware1",\s*"hardware2"\s*\);\s*'
                               r'variable teststring = "hardware_newstring";\s*',
                          cmd)

    def test_500_verify_diff(self):
        cmd = ["show_diff", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--other", OTHER_PERSONALITY]

        out = self.commandtest(cmd)
        self.searchoutput(out, r'Differences for Required Services:\s*'
                               r'missing Required Services in Personality aquilon/unixeng-test:\s*'
                               r'netmap\s*'
                               r'missing Required Services in Personality aquilon/eaitools:\s*'
                               r'chooser1\s*chooser2\s*chooser3',
                         cmd)
        self.searchoutput(out, r'Differences for Features:\s*'
                               r'missing Features in Personality aquilon/eaitools:\s*'
                               r'hostfeature\s*'
                               r'interfacefeature\s*',
                          cmd)

    def test_910_del_host_featue(self):
        cmd = ["unbind_feature", "--feature", HOSTFEATURE,
               "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

        cmd = ["del_feature", "--feature", HOSTFEATURE, "--type", "host"]
        self.noouttest(cmd)

    def test_920_del_hardware_feature(self):

        cmd = ["unbind_feature", "--feature", HARDWAREFEATURE,
               "--archetype", ARCHETYPE, "--justification=tcm=12345678", "--model", "hs21-8853l5u"]
        self.ignoreoutputtest(cmd)

        cmd = ["del_feature", "--feature", HARDWAREFEATURE, "--type", "hardware"]
        self.noouttest(cmd)

    def test_del_interface_feature(self):

        cmd = ["unbind_feature", "--feature", INTERFACEFEATURE,
               "--personality", PERSONALITY, "--interface", "eth0"]
        self.ignoreoutputtest(cmd)

        cmd = ["del_feature", "--feature", INTERFACEFEATURE, "--type", "interface"]
        self.ignoreoutputtest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
