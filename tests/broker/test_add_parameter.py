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
"""Module for testing the add parameter command."""

import json

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin
from broker.personalitytest import PersonalityTestMixin

test_metric = {
    '_20003': {
        'active': False,
        'class': 'system.swapUsed',
        'descr': 'Swap space used [%]',
        'latestonly': False,
        'name': 'SwapUsed',
        'period': 300,
        'smooth': {
            'maxdiff': 3.0,
            'maxtime': 3600,
            'typeString': False
        }
    }
}



class TestAddParameter(VerifyGrnsMixin, PersonalityTestMixin,
                       TestBrokerCommand):

    def check_match(self, out, expected, command):
        out = ' '.join(out.split())
        self.matchoutput(out, expected, command)

    def test_100_no_params_yet(self):
        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "No parameters found for personality aquilon/utpers-dev@next.",
                         command)

        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next",
                   "--format", "proto"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "No parameters found for personality aquilon/utpers-dev@next.",
                         command)

    def test_110_promote_utpers_dev(self):
        # Create the 'current' stage we can compare against
        self.noouttest(["promote", "--personality", "utpers-dev", "--archetype", "aquilon"])

    def test_111_setup_utpers_dev_basic(self):
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "espinfo/function", "--value", "crash"])
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "espinfo/users", "--value", "someusers, otherusers"])
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "espinfo/class", "--value", "INFRASTRUCTURE"])

    def test_115_show_basic_setup(self):
        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchoutput(out, "espinfo", command)

    def test_115_diff_stages(self):
        command = ["show_diff", "--personality", "utpers-dev", "--archetype", "aquilon",
                   "--personality_stage", "next", "--other_stage", "current"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Differences for Parameters for template espinfo:
              missing Parameters for template espinfo in Personality aquilon/utpers-dev@current:
                //class
                //function
                //users/0
                //users/1
            """, command)

    def test_120_promote_utpers_dev_basic(self):
        # Make sure the basic parameters are present in the current stage too
        self.noouttest(["promote", "--personality", "utpers-dev", "--archetype", "aquilon"])

    def test_125_show_defaults_proto(self):
        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--format", "proto"]
        # The defaults should not show up in protobuf output
        out = self.protobuftest(command, expect=3)
        for message in out:
            self.assertTrue(message.path.startswith("espinfo/"))

    def test_125_cat_promoted_basic_setup(self):
        command = ["cat", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--param_tmpl", "espinfo"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         'structure template personality/utpers-dev/espinfo;',
                         command)
        self.matchoutput(out, '"function" = "crash";', command)
        self.matchoutput(out, '"class" = "INFRASTRUCTURE";', command)
        self.searchoutput(out,
                          r'"users" = list\(\s*"someusers",\s*"otherusers"\s*\);',
                          command)

    def test_130_validate(self):
        command = ["validate_parameter", "--personality", "utpers-dev"]
        out = self.badrequesttest(command)
        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: windows \[required\]\s*'
                          r'Type: json\s*'
                          r'Template: windows\s*'
                          r'Activation: dispatch\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*'
                          r'Template: foo',
                          command)

    def test_140_add_actions(self):
        action1 = {
            "user": "user1",
            "command": "/bin/testaction",
        }
        action2 = {
            "user": "user2",
            "command": "/bin/testaction2",
            "timeout": 100,
        }

        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "actions/testaction",
                        "--value", json.dumps(action1)])
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "actions/testaction2",
                        "--value", json.dumps(action2)])

    def test_141_add_metric(self):
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon",
                        "--path", "monitoring/metric",
                        "--value", json.dumps(test_metric)])

    def test_145_show_params(self):
        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.check_match(out,
                         'Template: espinfo '
                         'class: "INFRASTRUCTURE" '
                         'function: "crash" '
                         'users: [ "someusers", "otherusers" ]',
                         command)
        self.check_match(out,
                         'testaction: { "command": "/bin/testaction", "user": "user1" }',
                         command)
        self.check_match(out,
                         'testaction2: { "command": "/bin/testaction2", "timeout": 100, "user": "user2" }',
                         command)

    def test_145_show_path_proto(self):
        command = ["show_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--personality_stage", "next",
                   "--format", "proto"]
        out = self.protobuftest(command, expect=5)
        params = {message.path: message.value for message in out}

        self.assertIn('espinfo/function', params)
        self.assertEqual(params['espinfo/function'], 'crash')

        self.assertIn('espinfo/class', params)
        self.assertEqual(params['espinfo/class'], 'INFRASTRUCTURE')

        self.assertIn('espinfo/users', params)
        self.assertEqual(params['espinfo/users'], 'someusers,otherusers')

        self.assertIn('actions', params)
        self.assertEqual(json.loads(params['actions']), {
            "testaction": {
                "command": "/bin/testaction",
                "user": "user1"
            },
            "testaction2": {
                "command": "/bin/testaction2",
                "user": "user2",
                "timeout": 100
            }
        })

        self.assertIn('monitoring/metric', params)
        self.assertEqual(json.loads(params['monitoring/metric']), test_metric)

    def test_145_cat_actions(self):
        command = ["cat", "--personality", "utpers-dev", "--archetype", "aquilon",
                   "--personality_stage", "next", "--param_tmpl", "actions"]
        out = self.commandtest(command)

        self.searchoutput(out,
                          r'"testaction" = nlist\(\s*'
                          r'"command", "/bin/testaction",\s*'
                          r'"user", "user1"\s*\)',
                          command)
        self.searchoutput(out,
                          r'"testaction2" = nlist\(\s*'
                          r'"command", "/bin/testaction2",\s*'
                          r'"timeout", 100,\s*'
                          r'"user", "user2"\s*\)\s*',
                          command)

    def test_145_cat_espinfo(self):
        command = ["cat", "--personality", "utpers-dev", "--archetype", "aquilon",
                   "--personality_stage", "next", "--param_tmpl", "espinfo"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'structure template personality/utpers-dev\+next/espinfo;\s*'
                          r'"class" = "INFRASTRUCTURE";\s*'
                          r'"function" = "crash";\s*'
                          r'"users" = list\(\s*'
                          r'"someusers",\s*'
                          r'"otherusers"\s*'
                          r'\);',
                          command)

    def test_145_cat_monitoring(self):
        command = ["cat", "--personality", "utpers-dev", "--archetype", "aquilon",
                   "--personality_stage", "next", "--param_tmpl", "monitoring"]
        out = self.commandtest(command)
        # Check the formatting of the floating point value
        self.searchoutput(out, r'"maxdiff", 3\.0+,', command)

    def test_150_add_all_required(self):
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "foo/testrequired",
                        "--value", "set"])
        self.noouttest(["add_parameter", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--path", "windows/windows",
                        "--value", '[{"duration": 8, "start": "08:00", "day": "Sun"}]'])

    def test_155_validate(self):
        command = ["validate_parameter", "--personality", "utpers-dev",
                   "--personality_stage", "next"]
        out = self.statustest(command)
        self.matchoutput(out, "All required parameters specified.", command)

    def test_200_add_noncompileable(self):
        command = ["add", "parameter", "--path", "foo", "--value", "bar",
                   "--archetype", "windows", "--personality", "generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Archetype windows is not compileable.", command)

    def test_200_missing_stage(self):
        command = ["add_parameter", "--personality", "nostage",
                   "--archetype", "aquilon",
                   "--path", "espinfo/function", "--value", "foobar",
                   "--personality_stage", "previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/nostage does not have "
                         "stage previous.", command)

    def test_200_bad_stage(self):
        command = ["add_parameter", "--personality", "nostage",
                   "--archetype", "aquilon",
                   "--path", "espinfo/function", "--value", "foobar",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

    def test_200_add_existing_path(self):
        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "espinfo/function", "--value", "crash"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter with path=function already exists",
                         command)

    def test_200_add_existing_json_path(self):
        value = json.dumps({"command": "/bin/testaction2",
                            "user": "user1",
                            "timeout": 100})
        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "actions/testaction2", "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter with path=testaction2 already exists",
                         command)

    def test_200_add_existing_leaf_path(self):
        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "actions/testaction/user", "--value", "user1"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter with path=testaction/user already exists",
                         command)

    def test_200_json_schema_validation(self):
        command = ["add_parameter", "--personality", "utpers-dev",
                   "--archetype", "aquilon",
                   "--path", "actions/testaction/badpath", "--value", 800]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Additional properties are not allowed", command)

    def test_200_cat_bad_template(self):
        command = ["cat", "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--param_tmpl", "bad-template"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown parameter template bad-template.",
                         command)

    def test_300_verify_diff(self):
        cmd = ["show_diff", "--archetype", "aquilon",
               "--personality", "utpers-dev", "--personality_stage", "next",
               "--other", "utpers-prod"]

        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Differences for Parameters for template actions:\s*'
                          r'missing Parameters for template actions in Personality aquilon/utpers-prod:\s*'
                          r'//testaction/command\s*'
                          r'//testaction/user\s*'
                          r'//testaction2/command\s*'
                          r'//testaction2/timeout\s*'
                          r'//testaction2/user\s*',
                          cmd)
        self.searchoutput(out,
                          r'Differences for Parameters for template espinfo:\s*'
                          r'missing Parameters for template espinfo in Personality aquilon/utpers-prod:\s*'
                          r'//users/1\s*'
                          r'matching Parameters for template espinfo with different values:\s*'
                          r'//function value=crash, othervalue=development\s*'
                          r'//users/0 value=someusers, othervalue=IT / TECHNOLOGY',
                          cmd)
        self.searchoutput(out,
                          r'Differences for Parameters for template foo:\s*'
                          r'missing Parameters for template foo in Personality aquilon/utpers-prod:\s*'
                          r'//testrequired\s*',
                          cmd)
        self.searchoutput(out,
                          r'Differences for Parameters for template monitoring:\s*'
                          r'missing Parameters for template monitoring in Personality aquilon/utpers-prod:\s*'
                          r'//metric/_20003/active\s*'
                          r'//metric/_20003/class\s*'
                          r'//metric/_20003/descr\s*'
                          r'//metric/_20003/latestonly\s*'
                          r'//metric/_20003/name\s*'
                          r'//metric/_20003/period\s*'
                          r'//metric/_20003/smooth/maxdiff\s*'
                          r'//metric/_20003/smooth/maxtime\s*'
                          r'//metric/_20003/smooth/typeString\s*',
                          cmd)

    def test_310_search_parameter_espinfo(self):
        cmd = ["search_parameter", "--archetype", "aquilon", "--path", "espinfo/function"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Host Personality: compileserver Archetype: aquilon\s*'
                          r'espinfo/function: "development"',
                          cmd)
        self.searchoutput(out,
                          r'Host Personality: inventory Archetype: aquilon\s*'
                          r'espinfo/function: "development"',
                          cmd)
        self.searchoutput(out,
                          r'Host Personality: unixeng-test Archetype: aquilon\s*'
                          r'Stage: current\s*'
                          r'espinfo/function: "development"',
                          cmd)
        self.searchoutput(out,
                          r'Host Personality: utpers-dev Archetype: aquilon\s*'
                          r'Stage: next\s*'
                          r'espinfo/function: "crash"',
                          cmd)
        self.searchoutput(out,
                          r'Host Personality: utpers-dev Archetype: aquilon\s*'
                          r'Stage: current\s*'
                          r'espinfo/function: "crash"',
                          cmd)

    def test_315_search_parameter_actions(self):
        cmd = ["search_parameter", "--archetype", "aquilon", "--path", "actions"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Host Personality: utpers-dev Archetype: aquilon\s*'
                          r'Stage: next\s*'
                          r'actions: {\s*'
                          r'"testaction": {\s*"command": "/bin/testaction",\s*"user": "user1"\s*},\s*'
                          r'"testaction2": {\s*"command": "/bin/testaction2",\s*"timeout": 100,\s*"user": "user2"\s*}\s*}',
                          cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddParameter)
    unittest.TextTestRunner(verbosity=2).run(suite)
