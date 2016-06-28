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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand

from .test_add_parameter_definition import default_param_defs


class TestDelParameterDefinition(TestBrokerCommand):

    def test_010_verify_precondition(self):
        self.check_plenary_exists("aquilon", "personality", "utunused/dev",
                                  "foo")

    def test_100_del_default(self):
        for path in default_param_defs:
            self.statustest(["del_parameter_definition", "--archetype", "aquilon",
                             "--path", "foo/" + path])

        for path in ["//foo/startslash", "foo/endslash//"]:
            self.statustest(["del_parameter_definition", "--archetype", "aquilon",
                             "--path", path])

    def test_105_verify_delete(self):
        command = ["search_parameter_definition", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Template: foo", command)

    def test_105_verify_plenary_gone(self):
        self.check_plenary_gone("aquilon", "personality", "utunused/dev", "foo")

    def test_110_del_feature(self):
        for path, params in default_param_defs.items():
            if "activation" in params:
                continue

            cmd = ["del_parameter_definition", "--feature", "pre_host",
                   "--type=host", "--path", path]
            self.noouttest(cmd)

        for path in ["//startslash", "endslash//"]:
            cmd = ["del_parameter_definition", "--feature", "pre_host",
                   "--type=host", "--path", path]
            self.noouttest(cmd)

    def test_115_verify_delete(self):
        cmd = ["search_parameter_definition", "--feature", "pre_host", "--type=host"]
        self.noouttest(cmd)

    def test_200_del_bad_feature_type(self):
        cmd = ["del_parameter_definition", "--feature", "pre_host",
               "--type=no-such-type", "--path=testpath"]
        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Unknown feature type 'no-such-type'. The valid "
                         "values are: hardware, host, interface.",
                         cmd)

    def test_200_del_bad_feature_path(self):
        cmd = ["del_parameter_definition", "--feature", "pre_host",
               "--type", "host", "--path", "path-does-not-exist"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out,
                         "Path path-does-not-exist does not match any "
                         "parameter definitions of host feature pre_host.",
                         cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelParameterDefinition)
    unittest.TextTestRunner(verbosity=2).run(suite)
