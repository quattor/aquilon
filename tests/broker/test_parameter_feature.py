#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

import unittest
from broker.brokertest import TestBrokerCommand

PERSONALITY = 'unixeng-test'
ARCHETYPE = 'aquilon'
HOSTFEATURE = 'hostfeature'
HARDWAREFEATURE = 'hardwarefeature'
INTERFACEFEATURE = 'interfacefeature'
OTHER_PERSONALITY = 'eaitools'

SHOW_CMD = ["show", "parameter", "--personality", PERSONALITY,
            "--personality_stage", "next"]

ADD_CMD = ["add", "parameter", "--personality", PERSONALITY]

UPD_CMD = ["update", "parameter", "--personality", PERSONALITY]

DEL_CMD = ["del", "parameter", "--personality", PERSONALITY]

CAT_CMD = ["cat", "--personality", PERSONALITY, "--personality_stage", "next"]

VAL_CMD = ["validate_parameter", "--personality", PERSONALITY]


class TestParameterFeature(TestBrokerCommand):

    def test_010_bind_host_feature(self):
        cmd = ["bind_feature", "--feature", HOSTFEATURE, "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

    def test_040_bind_hardware_feature(self):
        cmd = ["bind_feature", "--feature", HARDWAREFEATURE, "--personality", PERSONALITY,
               "--archetype", ARCHETYPE, "--justification=tcm=12345678", "--model", "hs21-8853"]
        self.ignoreoutputtest(cmd)

    def test_070_bind_interface_feature(self):
        cmd = ["bind_feature", "--feature", INTERFACEFEATURE,
               "--personality", PERSONALITY, "--interface", "eth0"]
        self.successtest(cmd)

    def test_090_verify_feature_proto_noerr(self):
        cmd = ["show", "parameter", "--personality", "utpersonality/dev", "--format=proto"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out, "Not Found: No parameters found for personality "
                         "aquilon/utpersonality/dev", cmd)

    def test_100_verify_cat_host_feature_defaults(self):
        cmd = CAT_CMD + ["--post_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"/system/features/hostfeature/testboolean" = true;\s*'
                          r'"/system/features/hostfeature/testfalsedefault" = false;\s*'
                          r'"/system/features/hostfeature/testfloat" = 100\.100;\s*'
                          r'"/system/features/hostfeature/testint" = 60;\s*'
                          r'"/system/features/hostfeature/testjson" = nlist\(\s*"val1",\s*"val2"\s*\);\s*'
                          r'"/system/features/hostfeature/testlist" = list\(\s*"val1",\s*"val2"\s*\);\s*'
                          r'"/system/features/hostfeature/teststring" = "default";\s*'
                          r'include \{ "features/hostfeature/config" \};',
                          cmd)

    def test_105_add_path_host_feature(self):
        path = "testdefault"
        value = "host_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

        path = "testlist"
        value = "host1,host2"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

    def test_110_add_path_host_feature_overrides(self):
        path = "testboolean"
        value = False
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

        path = "teststring"
        value = "override"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

        path = "testint"
        value = 0
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HOSTFEATURE]
        self.noouttest(cmd)

    def test_115_verify_host_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out, r'"hostfeature": {\s*'
                               r'"testboolean": false,\s*'
                               r'"testdefault": "host_feature",\s*'
                               r'"testint": 0,\s*'
                               r'"testlist": \[\s*"host1",\s*"host2"\s*\],\s*'
                               r'"teststring": "override"\s*', cmd)

    def test_120_verify_cat_host_feature(self):
        cmd = CAT_CMD + ["--post_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"/system/features/hostfeature/testboolean" = false;\s*'
                          r'"/system/features/hostfeature/testdefault" = "host_feature";\s*'
                          r'"/system/features/hostfeature/testfalsedefault" = false;\s*'
                          r'"/system/features/hostfeature/testfloat" = 100\.100;\s*'
                          r'"/system/features/hostfeature/testint" = 0;\s*'
                          r'"/system/features/hostfeature/testjson" = nlist\(\s*"val1",\s*"val2"\s*\);\s*'
                          r'"/system/features/hostfeature/testlist" = list\(\s*"host1",\s*"host2"\s*\);\s*'
                          r'"/system/features/hostfeature/teststring" = "override";\s*'
                          r'include \{ "features/hostfeature/config" \};',
                          cmd)

    # TODO: Move this to test_constraints_parameter
    def test_125_try_del_paramdef(self):
        cmd = ["del_parameter_definition", "--feature", "hostfeature", "--type=host",
               "--path=testdefault"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path testdefault used by following and cannot be deleted", cmd)

    def test_130_validate(self):
        cmd = VAL_CMD
        out = self.badrequesttest(cmd)

        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*',
                          cmd)
        self.searchoutput(out,
                          r'Feature Binding: hostfeature\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*',
                          cmd)
        self.searchoutput(out,
                          r'Feature Binding: hardwarefeature\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*',
                          cmd)
        self.searchoutput(out,
                          r'Feature Binding: interfacefeature\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*',
                          cmd)

    def test_140_unbound_feature(self):
        command = ["add_parameter", "--personality", PERSONALITY,
                   "--feature", "myfeature", "--path", "teststring",
                   "--value", "some_value"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Host Feature myfeature is not bound to "
                         "personality aquilon/unixeng-test@next.", command)

    def test_200_add_path_interface_feature(self):
        path = "testdefault"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", INTERFACEFEATURE]
        self.noouttest(cmd)

        path = "testlist"
        value = "intf1,intf2"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", INTERFACEFEATURE]
        self.noouttest(cmd)

    def test_210_verify_interface_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"interface": {\s*'
                          r'"interfacefeature": {\s*'
                          r'"testdefault": "interface_feature",\s*'
                          r'"testlist": \[\s*"intf1",\s*"intf2"\s*\]\s*'
                          r'}\s*}',
                          cmd)

    def test_220_verify_cat_interface_feature(self):
        cmd = CAT_CMD + ["--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"/system/features/interface/interfacefeature/testboolean" = true;\s*'
                          r'"/system/features/interface/interfacefeature/testdefault" = "interface_feature";\s*'
                          r'"/system/features/interface/interfacefeature/testfalsedefault" = false;\s*'
                          r'"/system/features/interface/interfacefeature/testfloat" = 100\.100;\s*'
                          r'"/system/features/interface/interfacefeature/testint" = 60;\s*'
                          r'"/system/features/interface/interfacefeature/testjson" = nlist\(\s*"val1",\s*"val2"\s*\);\s*'
                          r'"/system/features/interface/interfacefeature/testlist" = list\(\s*"intf1",\s*"intf2"\s*\);\s*'
                          r'"/system/features/interface/interfacefeature/teststring" = "default";\s*'
                          r'variable CURRENT_INTERFACE = "eth0";\s*'
                          r'include \{ "features/interface/interfacefeature/config" \};',
                          cmd)

    def test_260_add_existing(self):
        path = "testdefault"
        value = "interface_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value,
                         "--feature", INTERFACEFEATURE]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path=features/interface/interfacefeature/testdefault already exists.", cmd)

    def test_300_add_path_hardware_feature(self):
        path = "testdefault"
        value = "hardware_feature"
        feature = "hardwarefeature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", feature]
        self.noouttest(cmd)

        path = "testlist"
        value = "hardware1,hardware2"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", feature]
        self.noouttest(cmd)

    def test_310_verify_hardware_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"hardware": {\s*'
                          r'"hardwarefeature": {\s*'
                          r'"testdefault": "hardware_feature",\s*'
                          r'"testlist": \[\s*"hardware1",\s*"hardware2"\s*\]',
                          cmd)

    def test_310_verify_feature_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        params = self.protobuftest(cmd, expect=12)

        param_values = {}
        for param in params:
            param_values[param.path] = param.value

        self.assertEqual(set(param_values.keys()),
                         set(["espinfo/class",
                              "espinfo/function",
                              "espinfo/users",
                              "features/hostfeature/testboolean",
                              "features/hostfeature/testdefault",
                              "features/hostfeature/testint",
                              "features/hostfeature/testlist",
                              "features/hostfeature/teststring",
                              "features/hardware/hardwarefeature/testlist",
                              "features/hardware/hardwarefeature/testdefault",
                              "features/interface/interfacefeature/testlist",
                              "features/interface/interfacefeature/testdefault",
                             ]))

        self.assertEqual(param_values['features/hostfeature/testboolean'],
                         'False')
        self.assertEqual(param_values['features/hostfeature/teststring'],
                         'override')
        self.assertEqual(param_values['features/hostfeature/testint'],
                         '0')
        self.assertEqual(param_values['features/hostfeature/testlist'],
                         'host1,host2')
        self.assertEqual(param_values['features/hostfeature/testdefault'],
                         'host_feature')
        self.assertEqual(param_values['features/hardware/hardwarefeature/testlist'],
                         'hardware1,hardware2')
        self.assertEqual(param_values['features/hardware/hardwarefeature/testdefault'],
                         'hardware_feature')
        self.assertEqual(param_values['features/interface/interfacefeature/testlist'],
                         'intf1,intf2')
        self.assertEqual(param_values['features/interface/interfacefeature/testdefault'],
                         'interface_feature')

    def test_320_verify_cat_hardware_feature(self):
        cmd = CAT_CMD + ["--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"/system/features/hardware/hardwarefeature/testboolean" = true;\s*'
                          r'"/system/features/hardware/hardwarefeature/testdefault" = "hardware_feature";\s*'
                          r'"/system/features/hardware/hardwarefeature/testfalsedefault" = false;\s*'
                          r'"/system/features/hardware/hardwarefeature/testfloat" = 100\.100;\s*'
                          r'"/system/features/hardware/hardwarefeature/testint" = 60;\s*'
                          r'"/system/features/hardware/hardwarefeature/testjson" = nlist\(\s*"val1",\s*"val2"\s*\);\s*'
                          r'"/system/features/hardware/hardwarefeature/testlist" = list\(\s*"hardware1",\s*"hardware2"\s*\);\s*'
                          r'"/system/features/hardware/hardwarefeature/teststring" = "default";\s*',
                          cmd)
        self.searchoutput(out,
                          r'include \{\s*'
                          r'if \(\(value\("/hardware/manufacturer"\) == "ibm"\) &&\s*'
                          r'\(value\("/hardware/template_name"\) == "hs21-8853"\)\)\s*\{\s*'
                          r'if \(exists\("features/hardware/hardwarefeature/config"\)\) \{\s*'
                          r'"features/hardware/hardwarefeature/config";\s*'
                          r'\} else \{\s*'
                          r'"features/hardware/hardwarefeature";\s*'
                          r'\};\s*'
                          r'\} else \{\s*undef;\s*\};\s*\};',
                          cmd)

    def test_360_add_existing(self):
        path = "testdefault"
        value = "hardware_feature"
        cmd = ADD_CMD + ["--path", path, "--value", value, "--feature", HARDWAREFEATURE]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path=features/hardware/hardwarefeature/testdefault already exists", cmd)

    def test_370_upd_existing(self):
        path = "testdefault"
        value = "hardware_newstring"
        cmd = UPD_CMD + ["--path", path, "--value", value, "--feature", HARDWAREFEATURE]
        out = self.noouttest(cmd)

    def test_380_verify_hardware_feature(self):
        cmd = SHOW_CMD
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"hardware": {\s*'
                          r'"hardwarefeature": {\s*'
                          r'"testdefault": "hardware_newstring",\s*'
                          r'"testlist": \[\s*"hardware1",\s*"hardware2"\s*\]',
                          cmd)

    def test_390_verify_cat_hardware_feature(self):
        cmd = CAT_CMD + ["--pre_feature"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'"/system/features/hardware/hardwarefeature/testboolean" = true;\s*'
                          r'"/system/features/hardware/hardwarefeature/testdefault" = "hardware_newstring";\s*'
                          r'"/system/features/hardware/hardwarefeature/testfalsedefault" = false;\s*'
                          r'"/system/features/hardware/hardwarefeature/testfloat" = 100\.100;\s*'
                          r'"/system/features/hardware/hardwarefeature/testint" = 60;\s*'
                          r'"/system/features/hardware/hardwarefeature/testjson" = nlist\(\s*"val1",\s*"val2"\s*\);\s*'
                          r'"/system/features/hardware/hardwarefeature/testlist" = list\(\s*"hardware1",\s*"hardware2"\s*\);\s*'
                          r'"/system/features/hardware/hardwarefeature/teststring" = "default";\s*',
                          cmd)

    def test_500_verify_diff(self):
        cmd = ["show_diff", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--personality_stage", "next", "--other", OTHER_PERSONALITY]

        out = self.commandtest(cmd)
        self.searchoutput(out, r'Differences for Required Services:\s*'
                               r'missing Required Services in Personality aquilon/%s@next:\s*'
                               r'netmap\s*'
                               r'missing Required Services in Personality aquilon/eaitools@current:\s*'
                               r'chooser1\s*chooser2\s*chooser3' % PERSONALITY,
                          cmd)
        self.searchoutput(out, r'Differences for Features:\s*'
                               r'missing Features in Personality aquilon/eaitools@current:\s*'
                               r'hardwarefeature\s*'
                               r'hostfeature\s*'
                               r'interfacefeature\s*',
                          cmd)
        self.searchoutput(out, r'Differences for Parameters:\s*'
                               r'missing Parameters in Personality aquilon/eaitools@current:\s*'
                               r'//features/hardware/hardwarefeature/testdefault\s*'
                               r'//features/hardware/hardwarefeature/testlist/0\s*'
                               r'//features/hardware/hardwarefeature/testlist/1\s*'
                               r'//features/hostfeature/testboolean\s*'
                               r'//features/hostfeature/testdefault\s*'
                               r'//features/hostfeature/testint\s*'
                               r'//features/hostfeature/testlist/0\s*'
                               r'//features/hostfeature/testlist/1\s*'
                               r'//features/hostfeature/teststring\s*'
                               r'//features/interface/interfacefeature/testdefault\s*'
                               r'//features/interface/interfacefeature/testlist/0\s*'
                               r'//features/interface/interfacefeature/testlist/1\s*',
                          cmd)

    def test_600_add_same_name_feature(self):
        feature = "shinynew"
        for type in ["host", "hardware", "interface"]:
            cmd = ["add_parameter_definition", "--feature", feature, "--type", type,
                   "--path", "car", "--value_type", "string"]
            self.noouttest(cmd)

            cmd = ["bind_feature", "--feature", feature, "--personality", PERSONALITY]
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
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "bmwinterface"', cmd)
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "bmwhardware"', cmd)
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "bmwhost"', cmd)

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
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "audiinterface"', cmd)
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "audihardware"', cmd)
        self.searchoutput(out, r'"shinynew": {\s*'
                               r'"car": "audihost"', cmd)

    def test_910_del_host_featue_param(self):
        cmd = DEL_CMD + ["--path=testdefault", "--feature", HOSTFEATURE]
        self.noouttest(cmd)

    def test_915_unbind_host_featue(self):
        cmd = ["unbind_feature", "--feature", HOSTFEATURE, "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

    def test_920_del_hardware_feature_params(self):
        cmd = DEL_CMD + ["--path=testdefault", "--feature", HARDWAREFEATURE]
        self.noouttest(cmd)

    def test_925_unbind_hardware_feature(self):
        cmd = ["unbind_feature", "--feature", HARDWAREFEATURE, "--personality", PERSONALITY,
               "--archetype", ARCHETYPE, "--justification=tcm=12345678", "--model", "hs21-8853"]
        self.ignoreoutputtest(cmd)

    def test_930_del_interface_feature_params(self):
        cmd = DEL_CMD + ["--path=testdefault", "--feature", INTERFACEFEATURE]
        self.noouttest(cmd)

    def test_935_del_interface_feature(self):
        cmd = ["unbind_feature", "--feature", INTERFACEFEATURE, "--interface", "eth0",
               "--personality", PERSONALITY]
        self.ignoreoutputtest(cmd)

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
            cmd = ["unbind_feature", "--feature", feature, "--personality", PERSONALITY]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853"])
            self.successtest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
