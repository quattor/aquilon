#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand


class TestParameterConstraints(TestBrokerCommand):

    def test_100_archetype_validation(self):
        cmd = ["del_parameter_definition", "--archetype", "aquilon",
               "--path=espinfo/function"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path espinfo/function used by following and cannot be deleted", cmd)

    def test_110_feature_validation(self):
        cmd = ["del_parameter_definition", "--feature", "pre_host", "--type=host",
               "--path=teststring"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path teststring used by following and cannot be deleted", cmd)

    def test_120_update_breaks_json_schema(self):
        command = ["del_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--path", "actions/testaction/user"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "'user' is a required property", command)

    def test_130_prepare_host(self):
        command = ["reconfigure", "--hostname", "aquilon71.aqd-unittest.ms.com",
                   "--personality", "utpers-dev", "--personality_stage", "next",
                   "--buildstatus", "almostready"]
        self.successtest(command)

    def test_131_add_rebuild_required_almostready(self):
        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "foo/test_rebuild_required", "--value", "test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_132_validate_modifying_other_params_works(self):
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "espinfo/description",
                        "--value", "some description"])
        self.noouttest(["update_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "espinfo/description",
                        "--value", "new description"])
        self.noouttest(["del_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "espinfo/description"])

    def test_133_add_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "aquilon71.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "foo/test_rebuild_required", "--value", "test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_134_add_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "aquilon71.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "foo/test_rebuild_required", "--value", "test"]
        self.noouttest(command)

    def test_135_update_rebuild_required_non_ready(self):
        command = ["update_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "foo/test_rebuild_required", "--value", "test"]
        self.noouttest(command)

    def test_135_update_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "aquilon71.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        command = ["update_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "foo/test_rebuild_required", "--value", "test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_136_del_rebuild_required_ready(self):
        command = ["del_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--path", "foo/test_rebuild_required"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_137_del_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "aquilon71.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        self.noouttest(["del_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "foo/test_rebuild_required"])

    def test_140_del_required(self):
        self.noouttest(["del_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "espinfo/function"])

    def test_141_reconfigure_fail(self):
        command = ["reconfigure", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--personality", "utpers-dev", "--personality_stage", "next"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "'/system/personality/function' does not have an associated value", command)
        self.matchoutput(err, "BUILD FAILED", command)

    def test_145_verify_stage_diff(self):
        # The parameter should still be present in 'current'
        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "current"]
        out = self.commandtest(command)
        self.matchoutput(out, 'function: "crash"', command)

        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchclean(out, 'function', command)

    def test_149_add_all_required(self):
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "espinfo/function",
                        "--value", "crash"])

    def test_200_proto_noparam(self):
        cmd = ["show", "parameter", "--personality", "utunused/dev", "--format=proto"]
        out = self.notfoundtest(cmd)
        self.matchoutput(out, "Not Found: No parameters found for personality "
                         "aquilon/utunused/dev", cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
