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
"""Module for testing parameter support for features."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
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

SHOW_CMD = ["show", "parameter", "--personality", PERSONALITY]

ADD_CMD = ["add", "parameter", "--personality", PERSONALITY]

UPD_CMD = ["update", "parameter", "--personality", PERSONALITY]

DEL_CMD = ["del", "parameter", "--personality", PERSONALITY]

CAT_CMD = ["cat", "--personality", PERSONALITY]

VAL_CMD = ["validate_parameter", "--personality", PERSONALITY]


class TestParameterFeature(TestBrokerCommand):

    def test_000_add_host_feature(self):
        type = "host"
        cmd = ["add_feature", "--feature", HOSTFEATURE, "--type", type, "--post_personality"]
        self.ignoreoutputtest(cmd)

    def test_010_bind_host_feature(self):
        cmd = ["bind_feature", "--feature", HOSTFEATURE, "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)
        self.load_paramdefs(HOSTFEATURE, 'host')

    def test_030_add_hardware_feature(self):
        type = "hardware"
        cmd = ["add_feature", "--feature", HARDWAREFEATURE, "--type", type]
        self.ignoreoutputtest(cmd)

    def test_040_bind_hardware_feature(self):
        cmd = ["bind_feature", "--feature", HARDWAREFEATURE, "--personality", PERSONALITY,
               "--archetype", ARCHETYPE, "--justification=tcm=12345678", "--model", "hs21-8853l5u"]
        self.ignoreoutputtest(cmd)
        self.load_paramdefs(HARDWAREFEATURE, 'hardware')

    def test_060_add_interface_feature(self):
        type = "interface"
        cmd = ["add_feature", "--feature", INTERFACEFEATURE, "--type", type]
        self.ignoreoutputtest(cmd)

    def test_070_bind_interface_feature(self):
        cmd = ["bind_feature", "--feature", INTERFACEFEATURE,
               "--personality", PERSONALITY, "--interface", "eth0"]
        self.successtest(cmd)

        cmd = ["bind_feature", "--feature", INTERFACEFEATURE,
               "--personality", PERSONALITY, "--interface", "eth1"]
        self.successtest(cmd)

        self.load_paramdefs(INTERFACEFEATURE, 'interface')

    def test_090_verify_feature_proto_noerr(self):
        cmd = ["show", "parameter", "--personality", "utpersonality/dev", "--format=proto"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out, "Not Found: No parameters found for personality utpersonality/dev",
                         cmd)

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
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

        path = "testlist"
        value = "host1,host2"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

    def test_110_verify_host_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"hostfeature": {\s*'
                               r'"testlist": "host1,host2",\s*'
                               r'"teststring": "host_feature"', cmd)

    def test_120_verify_cat_host_feature(self):
        cmd = CAT_CMD + ["--post_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"/system/features/hostfeature/testdefault" = "defaultval";\s*'
                               r'"/system/features/hostfeature/testlist" = list\(\s*'
                               r'"host1",\s*"host2"\s*\);\s*'
                               r'"/system/features/hostfeature/teststring" = "host_feature";\s*'
                               r'include \{ "features/hostfeature/config" \};',
                          cmd)

    def test_130_validate(self):
        cmd = VAL_CMD
        out = self.badrequesttest(cmd)

        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*',
                          cmd)
        self.searchoutput(out,
                          r'Feature Binding : hostfeature\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*'
                          r'Rebuild Required: False\s*',
                          cmd)
        self.searchoutput(out,
                          r'Feature Binding : hardwarefeature\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*'
                          r'Rebuild Required: False\s*',
                          cmd)
        self.searchoutput(out,
                          r'Feature Binding : interfacefeature\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*'
                          r'Rebuild Required: False\s*',
                          cmd)

    def test_200_add_path_interface_feature(self):
        path = "teststring"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", INTERFACEFEATURE,
                         "--interface=eth0"]
        self.noouttest(cmd)

        path = "testlist"
        value = "intf1,intf2"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", INTERFACEFEATURE,
                         "--interface=eth0"]
        self.noouttest(cmd)

    def test_200_add_path_interface_feature_2(self):
        path = "teststring"
        value = "other_value"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", INTERFACEFEATURE,
                         "--interface=eth1"]
        self.noouttest(cmd)

    def test_210_verify_interface_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"interface": {\s*'
                               r'"interfacefeature": {\s*'
                               r'"eth1": {\s*'
                               r'"teststring": "other_value"\s*'
                               r'},\s*'
                               r'"eth0": {\s*'
                               r'"testlist": "intf1,intf2",\s*'
                               r'"teststring": "interface_feature"', cmd)

    def test_220_verify_cat_interface_feature(self):
        cmd = CAT_CMD + ["--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"/system/features/interface/interfacefeature/{eth0}/testdefault" = "defaultval";\s*'
                               r'"/system/features/interface/interfacefeature/{eth0}/testlist" = list\(\s*'
                               r'"intf1",\s*"intf2"\s*\);\s*'
                               r'"/system/features/interface/interfacefeature/{eth0}/teststring" = "interface_feature";\s*'
                               r'variable CURRENT_INTERFACE = "eth0";\s*'
                               r'include \{ "features/interface/interfacefeature/config" \};',
                          cmd)
        self.searchoutput(out, r'"/system/features/interface/interfacefeature/{eth1}/testdefault" = "defaultval";\s*'
                               r'"/system/features/interface/interfacefeature/{eth1}/teststring" = "other_value";\s*'
                               r'variable CURRENT_INTERFACE = "eth1";\s*'
                               r'include \{ "features/interface/interfacefeature/config" \};',
                          cmd)

    def test_260_add_existing(self):
        path = "teststring"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", INTERFACEFEATURE, "--interface=eth0"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path=features/interface/interfacefeature/eth0/teststring already exists.", cmd)

    def test_300_add_path_hardware_feature(self):
        path = "teststring"
        value = "hardware_feature"
        feature = "hardwarefeature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", feature,
                         "--model", "hs21-8853l5u"]
        self.noouttest(cmd)

        path = "testlist"
        value = "hardware1,hardware2"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", feature, "--model", "hs21-8853l5u"]
        self.noouttest(cmd)

    def test_310_verify_hardware_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"hardware": {\s*'
                               r'"hardwarefeature": {\s*'
                               r'"hs21-8853l5u": {\s*'
                               r'"testlist": "hardware1,hardware2",\s*'
                               r'"teststring": "hardware_feature"', cmd)

    def test_310_verify_feature_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 10)
        params = p.parameters

        param_values = {}
        for param in params:
            param_values[param.path] = param.value

        self.failUnless('features/hostfeature/teststring' in param_values)
        self.failUnlessEqual(param_values['features/hostfeature/teststring'],
                             'host_feature')
        self.failUnless('features/hostfeature/testlist' in param_values)
        self.failUnlessEqual(param_values['features/hostfeature/testlist'],
                             'host1,host2')
        self.failUnless('features/hardware/hardwarefeature/hs21-8853l5u/teststring'
                        in param_values)
        self.failUnlessEqual(param_values['features/hardware/hardwarefeature/hs21-8853l5u/teststring'],
                             'hardware_feature')
        self.failUnless('features/hardware/hardwarefeature/hs21-8853l5u/testlist'
                        in param_values)
        self.failUnlessEqual(param_values['features/hardware/hardwarefeature/hs21-8853l5u/testlist'],
                             'hardware1,hardware2')
        self.failUnless('features/interface/interfacefeature/eth0/teststring'
                        in param_values)
        self.failUnlessEqual(param_values['features/interface/interfacefeature/eth0/teststring'],
                             'interface_feature')
        self.failUnless('features/interface/interfacefeature/eth0/testlist' in
                        param_values)
        self.failUnlessEqual(param_values['features/interface/interfacefeature/eth0/testlist'],
                             'intf1,intf2')

    def test_320_verify_cat_hardware_feature(self):
        cmd = CAT_CMD + ["--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"/system/features/hardware/hardwarefeature/{hs21-8853l5u}/testdefault" = "defaultval";\s*'
                               r'"/system/features/hardware/hardwarefeature/{hs21-8853l5u}/testlist" = list\(\s*'
                               r'"hardware1",\s*"hardware2"\s*\);\s*'
                               r'"/system/features/hardware/hardwarefeature/{hs21-8853l5u}/teststring" = "hardware_feature";\s*',
                          cmd)
        self.searchoutput(out, r'include \{\s*'
                               r'if \(\(value\("/hardware/manufacturer"\) == "ibm"\) &&\s*'
                               r'\(value\("/hardware/template_name"\) == "hs21-8853l5u"\)\)\{\s*'
                               r'return\("features/hardware/hardwarefeature"\)\s*'
                               r'\} else\{ return\(undef\); \};\s*};',
                          cmd)

    def test_360_add_existing(self):
        path = "teststring"
        value = "hardware_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HARDWAREFEATURE, "--model", "hs21-8853l5u"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path=features/hardware/hardwarefeature/hs21-8853l5u/teststring already exists", cmd)

    def test_370_upd_existing(self):
        path = "teststring"
        value = "hardware_newstring"
        cmd = UPD_CMD + ["--path", path, "--value", value, "--feature", HARDWAREFEATURE, "--model", "hs21-8853l5u"]
        out = self.noouttest(cmd)

    def test_380_verify_hardware_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"hardware": {\s*'
                               r'"hardwarefeature": {\s*'
                               r'"hs21-8853l5u": {\s*'
                               r'"testlist": "hardware1,hardware2",\s*'
                               r'"teststring": "hardware_newstring"', cmd)

    def test_390_verify_cat_hardware_feature(self):
        cmd = CAT_CMD + ["--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"/system/features/hardware/hardwarefeature/{hs21-8853l5u}/testdefault" = "defaultval";\s*'
                               r'"/system/features/hardware/hardwarefeature/{hs21-8853l5u}/testlist" = list\(\s*'
                               r'"hardware1",\s*"hardware2"\s*\);\s*'
                               r'"/system/features/hardware/hardwarefeature/{hs21-8853l5u}/teststring" = "hardware_newstring";\s*',
                          cmd)

    def test_500_verify_diff(self):
        cmd = ["show_diff", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--other", OTHER_PERSONALITY]

        out = self.commandtest(cmd)
        self.searchoutput(out, r'Differences for Required Services:\s*'
                               r'missing Required Services in Personality aquilon/%s:\s*'
                               r'netmap\s*'
                               r'missing Required Services in Personality aquilon/eaitools:\s*'
                               r'chooser1\s*chooser2\s*chooser3' % PERSONALITY,
                          cmd)
        self.searchoutput(out, r'Differences for Features:\s*'
                               r'missing Features in Personality aquilon/eaitools:\s*'
                               r'hardwarefeature\s*'
                               r'hostfeature\s*'
                               r'interfacefeature\s*',
                          cmd)
        self.searchoutput(out, r'Differences for Parameters:\s*'
                               r'missing Parameters in Personality aquilon/eaitools:\s*'
                               r'//features/hardware/hardwarefeature/hs21-8853l5u/testlist\s*'
                               r'//features/hardware/hardwarefeature/hs21-8853l5u/teststring\s*'
                               r'//features/hostfeature/testlist\s*'
                               r'//features/hostfeature/teststring\s*'
                               r'//features/interface/interfacefeature/eth0/testlist\s*'
                               r'//features/interface/interfacefeature/eth0/teststring\s*'
                               r'//features/interface/interfacefeature/eth1/teststring\s*',
                          cmd)

    def test_600_add_same_name_feature(self):
        feature = "shinynew"
        for type in ["host", "hardware", "interface"]:
            cmd = ["add_feature", "--feature", feature, "--type", type]
            self.ignoreoutputtest(cmd)

            cmd = ["add_parameter_definition", "--feature", feature, "--type", type,
                   "--path", "car", "--value_type", "string"]
            self.noouttest(cmd)

            cmd = ["bind_feature", "--feature", feature, "--personality", PERSONALITY]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853l5u"])
            self.successtest(cmd)

    def test_610_add_same_name_feature_parameter(self):
        feature = "shinynew"
        path = "car"
        for type in ["host", "hardware", "interface"]:
            cmd = ADD_CMD + ["--path", path, "--value", 'bmw' + type, "--feature", feature]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853l5u"])
            self.successtest(cmd)

    def test_620_verify_name_feature_parameter(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"interface": {\s*'
                               r'"shinynew": {\s*'
                               r'"eth0": {\s*'
                               r'"car": "bmwinterface"', cmd)
        self.searchoutput(out, r'"hardware": {\s*'
                               r'"shinynew": {\s*'
                               r'"hs21-8853l5u": {\s*'
                               r'"car": "bmwhardware"', cmd)
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "bmwhost"', cmd)

    def test_630_upd_same_name_feature_parameter(self):
        feature = "shinynew"
        path = "car"
        for type in ["host", "hardware", "interface"]:
            cmd = UPD_CMD + ["--path", path, "--value", 'audi' + type, "--feature", feature]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853l5u"])
            self.successtest(cmd)

    def test_640_verify_name_feature_parameter(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"interface": {\s*'
                               r'"shinynew": {\s*'
                               r'"eth0": {\s*'
                               r'"car": "audiinterface"', cmd)
        self.searchoutput(out, r'"hardware": {\s*'
                               r'"shinynew": {\s*'
                               r'"hs21-8853l5u": {\s*'
                               r'"car": "audihardware"', cmd)
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "audihost"', cmd)

    def test_910_del_host_featue_param(self):
        cmd = DEL_CMD + ["--path=teststring", "--feature", HOSTFEATURE]
        self.noouttest(cmd)

    def test_915_unbind_host_featue(self):
        cmd = ["unbind_feature", "--feature", HOSTFEATURE, "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

        cmd = ["del_feature", "--feature", HOSTFEATURE, "--type", "host"]
        self.noouttest(cmd)

    def test_920_del_hardware_feature_params(self):
        cmd = DEL_CMD + ["--path=teststring", "--feature", HARDWAREFEATURE, "--model", "hs21-8853l5u"]
        self.noouttest(cmd)

    def test_925_unbind_hardware_feature(self):
        cmd = ["unbind_feature", "--feature", HARDWAREFEATURE, "--personality", PERSONALITY,
               "--archetype", ARCHETYPE, "--justification=tcm=12345678", "--model", "hs21-8853l5u"]
        self.ignoreoutputtest(cmd)

        cmd = ["del_feature", "--feature", HARDWAREFEATURE, "--type=hardware"]
        self.noouttest(cmd)

    def test_930_del_interface_feature_params(self):
        cmd = DEL_CMD + ["--path=teststring", "--feature", INTERFACEFEATURE, "--interface=eth0"]
        self.noouttest(cmd)

    def test_935_del_interface_feature(self):
        cmd = ["unbind_feature", "--feature", INTERFACEFEATURE, "--interface", "eth0",
               "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

        cmd = ["unbind_feature", "--feature", INTERFACEFEATURE, "--interface", "eth1",
               "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

        cmd = ["del_feature", "--feature", INTERFACEFEATURE, "--type", "interface"]
        self.ignoreoutputtest(cmd)

    def test_950_del_same_name_feature_parameter(self):
        feature = "shinynew"
        path = "car"
        for type in ["host", "hardware", "interface"]:
            cmd = DEL_CMD + ["--path", path, "--feature", feature]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853l5u"])
            self.noouttest(cmd)

    def test_960_verify_same_name_feature_parameter(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchclean(out, "shinynew", cmd)
        self.searchclean(out, "car", cmd)

    def test_970_unbind_same_name_feature(self):
        feature = "shinynew"
        for type in ["host", "hardware", "interface"]:
            cmd = ["unbind_feature", "--feature", feature, "--personality", PERSONALITY]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853l5u"])
            self.successtest(cmd)

            cmd = ["del_feature", "--feature", feature, "--type", type]
            self.ignoreoutputtest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
