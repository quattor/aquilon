#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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


class TestAddParameterFeature(TestBrokerCommand):

    def test_010_unbound_feature(self):
        # The feature is bound to the archetype, but not to the personality, so
        # parameters cannot work
        command = ["add_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon", "--feature", "bios_setup",
                   "--path", "testdefault", "--value", "testvalue"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Hardware Feature bios_setup is not bound to "
                         "personality aquilon/compileserver.", command)

    def test_020_bind_hardware_feature(self):
        self.statustest(["bind_feature", "--feature", "bios_setup",
                         "--personality", "compileserver", "--archetype", "aquilon",
                         "--model", "hs21-8853"])

    def test_100_add_hw_params(self):
        self.noouttest(["add_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "bios_setup",
                        "--path", "testdefault", "--value", "hardware_feature"])
        self.noouttest(["add_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "bios_setup",
                        "--path", "testlist", "--value", "hardware1,hardware2"])

    def test_105_show_hw_params(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup\s*'
                          r'testdefault: "hardware_feature"\s*'
                          r'testlist: \[\s*"hardware1",\s*"hardware2"\s*\]',
                          command)

    def test_105_show_hw_params_proto(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon", "--format", "proto"]
        params = self.protobuftest(command, expect=6)

        param_values = {}
        for param in params:
            param_values[param.path] = param.value

        self.assertEqual(set(param_values.keys()),
                         set(["espinfo/class",
                              "espinfo/function",
                              "espinfo/users",
                              "features/hardware/bios_setup/testdefault",
                              "features/hardware/bios_setup/testlist",
                              "windows/windows",
                             ]))

        self.assertEqual(param_values['features/hardware/bios_setup/testlist'],
                         'hardware1,hardware2')
        self.assertEqual(param_values['features/hardware/bios_setup/testdefault'],
                         'hardware_feature')

    def test_105_cat_hw_params(self):
        command = ["cat", "--personality", "compileserver", "--archetype", "aquilon",
                   "--pre_feature"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"/system/features/hardware/bios_setup/testboolean" = true;\s*'
                          r'"/system/features/hardware/bios_setup/testdefault" = "hardware_feature";\s*'
                          r'"/system/features/hardware/bios_setup/testfalsedefault" = false;\s*'
                          r'"/system/features/hardware/bios_setup/testfloat" = 100\.100;\s*'
                          r'"/system/features/hardware/bios_setup/testint" = 60;\s*'
                          r'"/system/features/hardware/bios_setup/testjson" = nlist\(\s*'
                          r'"key",\s*"param_key",\s*'
                          r'"values",\s*list\(\s*0\s*\)\s*\);\s*'
                          r'"/system/features/hardware/bios_setup/testlist" = list\(\s*"hardware1",\s*"hardware2"\s*\);\s*'
                          r'"/system/features/hardware/bios_setup/teststring" = "default";\s*',
                          command)

    def test_105_diff_hw_params(self):
        command = ["show_diff", "--archetype", "aquilon",
                   "--personality", "compileserver", "--other", "utpers-dev"]
        out = self.commandtest(command)

        self.searchoutput(out,
                          r'Differences for Features:\s*'
                          r'missing Features in Personality aquilon/utpers-dev@current:\s*'
                          r'bios_setup\s*',
                          command)

        self.searchoutput(out,
                          r'Differences for Parameters for hardware feature bios_setup:\s*'
                          r'missing Parameters for hardware feature bios_setup in Personality aquilon/utpers-dev@current:\s*'
                          r'//testdefault\s*'
                          r'//testlist/0\s*'
                          r'//testlist/1\s*',
                          command)

    def test_110_add_iface_params(self):
        self.noouttest(["add_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "src_route",
                        "--path", "testdefault",
                        "--value", "interface_feature"])
        self.noouttest(["add_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "src_route",
                        "--path", "testlist",
                        "--value", "iface1,iface2"])

    def test_115_show_iface_params(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route\s*'
                          r'testdefault: "interface_feature"\s*'
                          r'testlist: \[\s*"iface1",\s*"iface2"\s*\]\s*',
                          command)

    def test_115_show_iface_params_proto(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon", "--format", "proto"]
        params = self.protobuftest(command, expect=8)

        param_values = {}
        for param in params:
            param_values[param.path] = param.value

        self.assertEqual(set(param_values.keys()),
                         set(["espinfo/class",
                              "espinfo/function",
                              "espinfo/users",
                              "features/hardware/bios_setup/testdefault",
                              "features/hardware/bios_setup/testlist",
                              "features/interface/src_route/testdefault",
                              "features/interface/src_route/testlist",
                              "windows/windows",
                             ]))

        self.assertEqual(param_values['features/interface/src_route/testlist'],
                         'iface1,iface2')
        self.assertEqual(param_values['features/interface/src_route/testdefault'],
                         'interface_feature')

    def test_115_cat_iface_params(self):
        command = ["cat", "--personality", "compileserver", "--archetype", "aquilon",
                   "--pre_feature"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"/system/features/interface/src_route/testboolean" = true;\s*'
                          r'"/system/features/interface/src_route/testdefault" = "interface_feature";\s*'
                          r'"/system/features/interface/src_route/testfalsedefault" = false;\s*'
                          r'"/system/features/interface/src_route/testfloat" = 100\.100;\s*'
                          r'"/system/features/interface/src_route/testint" = 60;\s*'
                          r'"/system/features/interface/src_route/testjson" = nlist\(\s*'
                          r'"key",\s*"param_key",\s*'
                          r'"values",\s*list\(\s*0\s*\)\s*\);\s*'
                          r'"/system/features/interface/src_route/testlist" = list\(\s*"iface1",\s*"iface2"\s*\);\s*'
                          r'"/system/features/interface/src_route/teststring" = "default";\s*',
                          command)

    def test_115_diff_iface_params(self):
        command = ["show_diff", "--archetype", "aquilon",
                   "--personality", "compileserver", "--other", "utpers-dev"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Differences for Features:\s*'
                          r'missing Features in Personality aquilon/utpers-dev@current:\s*'
                          r'bios_setup\s*'
                          r'src_route\s*',
                          command)
        self.searchoutput(out,
                          r'Differences for Parameters for interface feature src_route:\s*'
                          r'missing Parameters for interface feature src_route in Personality aquilon/utpers-dev@current:\s*'
                          r'//testdefault\s*'
                          r'//testlist/0\s*'
                          r'//testlist/1\s*',
                          command)

    def test_200_unbound_feature(self):
        command = ["add_parameter", "--personality", "unixeng-test",
                   "--feature", "unused_no_params", "--path", "teststring",
                   "--value", "some_value"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Host Feature unused_no_params is not bound to "
                         "personality aquilon/unixeng-test@next.", command)

    def test_200_add_hw_existing(self):
        command = ["add_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon", "--feature", "bios_setup",
                   "--path", "testdefault", "--value", "hardware_feature"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Parameter with path=testdefault already exists",
                         command)

    def test_200_add_iface_existing(self):
        command = ["add_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon", "--feature", "src_route",
                   "--path", "testdefault", "--value", "interface_feature"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Parameter with path=testdefault already exists",
                         command)

    def test_300_validate(self):
        command = ["validate_parameter", "--personality", "compileserver"]
        out = self.badrequesttest(command)

        self.searchoutput(out,
                          r'Feature Binding: bios_setup\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*',
                          command)
        self.searchoutput(out,
                          r'Feature Binding: src_route\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*',
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
