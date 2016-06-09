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


class TestUpdateParameterFeature(TestBrokerCommand):

    def test_100_hw_update(self):
        self.noouttest(["update_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "bios_setup",
                        "--path", "testdefault",
                        "--value", "hardware_newstring"])

    def test_105_show_hw_params(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup\s*'
                          r'testdefault: "hardware_newstring"\s*'
                          r'testlist: \[\s*"hardware1",\s*"hardware2"\s*\]\s*',
                          command)

    def test_105_cat_hw_params(self):
        command = ["cat", "--personality", "compileserver", "--archetype", "aquilon",
                   "--pre_feature"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"/system/features/hardware/bios_setup/testboolean" = true;\s*'
                          r'"/system/features/hardware/bios_setup/testdefault" = "hardware_newstring";\s*'
                          r'"/system/features/hardware/bios_setup/testfalsedefault" = false;\s*'
                          r'"/system/features/hardware/bios_setup/testfloat" = 100\.100;\s*'
                          r'"/system/features/hardware/bios_setup/testint" = 60;\s*'
                          r'"/system/features/hardware/bios_setup/testjson" = nlist\(\s*'
                          r'"key",\s*"param_key",\s*'
                          r'"values",\s*list\(\s*0\s*\)\s*\);\s*'
                          r'"/system/features/hardware/bios_setup/testlist" = list\(\s*"hardware1",\s*"hardware2"\s*\);\s*'
                          r'"/system/features/hardware/bios_setup/teststring" = "default";\s*',
                          command)

    def test_110_iface_update(self):
        self.noouttest(["update_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "src_route",
                        "--path", "testlist",
                        "--value", "newiface1,newiface2,newiface3"])

    def test_115_show_iface_params(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route\s*'
                          r'testdefault: "interface_feature"\s*'
                          r'testlist: \[\s*"newiface1",\s*"newiface2",\s*"newiface3"\s*\]\s*',
                          command)

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
                          r'"/system/features/interface/src_route/testlist" = list\(\s*"newiface1",\s*"newiface2",\s*"newiface3"\s*\);\s*'
                          r'"/system/features/interface/src_route/teststring" = "default";\s*',
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
