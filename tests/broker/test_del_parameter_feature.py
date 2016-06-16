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


class TestDelParameterFeature(TestBrokerCommand):

    def test_100_del_hw_params(self):
        self.noouttest(["del_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "bios_setup",
                        "--path", "testdefault"])

    def test_105_show_hw_param_gone(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup\s*'
                          r'testlist: \[\s*"hardware1",\s*"hardware2"\s*\]',
                          command)

    def test_105_cat_hw_param_gone(self):
        command = ["cat", "--personality", "compileserver", "--archetype", "aquilon",
                   "--pre_feature"]
        out = self.commandtest(command)
        self.matchclean(out, "bios_setup/testdefault", command)

    def test_110_del_iface_params(self):
        self.noouttest(["del_parameter", "--personality", "compileserver",
                        "--archetype", "aquilon", "--feature", "src_route",
                        "--path", "testlist"])

    def test_115_cat_iface_param_gone(self):
        command = ["cat", "--personality", "compileserver", "--archetype", "aquilon",
                   "--pre_feature"]
        out = self.commandtest(command)
        # The default value should be there
        self.searchoutput(out,
                          r'"/system/features/interface/src_route/testlist" = list\(\s*"val1",\s*"val2"\s*\);\s*',
                          command)

    def test_120_del_host_params(self):
        self.noouttest(["del_parameter", "--personality", "inventory",
                        "--archetype", "aquilon", "--feature", "pre_host",
                        "--path", "testdefault"])

    def test_121_del_json_array_member(self):
        self.noouttest(["del_parameter", "--personality", "inventory",
                        "--archetype", "aquilon", "--feature", "pre_host",
                        "--path", "testjson/values/1"])

    def test_125_cat_host_param(self):
        command = ["cat", "--personality", "inventory", "--pre_feature"]
        out = self.commandtest(command)
        self.matchclean(out, "pre_host/testdefault", command)
        self.searchoutput(out,
                          r'"/system/features/pre_host/testjson" = nlist\(\s*'
                          r'"key",\s*"new_key",\s*'
                          r'"values",\s*list\(\s*1,\s*3\s*\)\s*\);\s*',
                          command)

    def test_130_del_same_feature_name_parameter(self):
        for type in ["host", "hardware", "interface"]:
            self.statustest(["del_parameter", "--personality", "inventory",
                             "--feature", "shinynew", "--type", type,
                             "--path", "car"])

    def test_135_verify_same_feature_name_parameter(self):
        command = ["show_parameter", "--personality", "inventory"]
        out = self.commandtest(command)
        self.searchclean(out, "shinynew", command)
        self.searchclean(out, "car", command)

    def test_200_json_index_invalid(self):
        command = ["del_parameter", "--personality", "inventory",
                   "--archetype", "aquilon", "--feature", "pre_host",
                   "--path", "testjson/values/2"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "No parameter of path=testjson/values/2 defined.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelParameterFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
