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
"""Module for testing parameter support."""

import json

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand

PERSONALITY = 'testpersona/dev'

ARCHETYPE = 'aquilon'
OTHER_PERSONALITY = 'utpers-dev'


SHOW_CMD = ["show", "parameter", "--personality", PERSONALITY,
            "--personality_stage", "next"]

ADD_CMD = ["add", "parameter", "--personality", PERSONALITY]

UPD_CMD = ["update", "parameter", "--personality", PERSONALITY]

DEL_CMD = ["del", "parameter", "--personality", PERSONALITY]

CAT_CMD = ["cat", "--personality", PERSONALITY, "--personality_stage", "next"]

VAL_CMD = ["validate_parameter", "--personality", PERSONALITY,
           "--personality_stage", "next"]

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


class TestParameter(TestBrokerCommand):

    def check_match(self, out, expected, command):
        out = ' '.join(out.split())
        self.matchoutput(out, expected, command)

    def check_match_clean(self, out, expected, command):
        out = ' '.join(out.split())
        self.matchclean(out, expected, command)

    def test_000_verify_preload(self):

        cmd = ["add_personality", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--eon_id=2", "--host_environment=dev", "--comment", "tests parameters",
               "--staged"]
        self.noouttest(cmd)

        cmd = ["show_parameter", "--personality", PERSONALITY, "--archetype",
               ARCHETYPE, "--personality_stage", "next"]
        err = self.notfoundtest(cmd)
        self.matchoutput(err,
                         "No parameters found for personality %s/%s@next." %
                         (ARCHETYPE, PERSONALITY), cmd)

        cmd = ["show_parameter", "--personality", PERSONALITY, "--archetype",
               ARCHETYPE, "--personality_stage", "next", "--format", "proto"]
        err = self.notfoundtest(cmd)
        self.matchoutput(err,
                         "No parameters found for personality %s/%s@next." %
                         (ARCHETYPE, PERSONALITY), cmd)

    def test_010_promote(self):
        self.noouttest(["promote", "--personality", PERSONALITY,
                        "--archetype", "aquilon"])

    def test_100_add_testaction(self):
        path = "actions/testaction"
        value = {"user": "user1", "command": "/bin/testaction"}
        command = ADD_CMD + ["--path", path, "--value", json.dumps(value)]
        self.noouttest(command)

    def test_105_verify_testaction(self):
        action = "testaction"
        expected = 'actions: { "%s": { "command": "/bin/%s", "user": "user1" } }' % (action, action)
        out = self.commandtest(SHOW_CMD)
        self.check_match(out, expected, SHOW_CMD)

    def test_105_verify_testaction_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        params = self.protobuftest(cmd, expect=1)
        self.assertEqual(params[0].path, 'actions')
        self.assertEqual(json.loads(params[0].value), {
            "testaction": {
                "command": "/bin/testaction",
                "user": "user1"
            }
        })

    def test_110_add_noncompileable(self):
        command = ["add", "parameter", "--path", "foo", "--value", "bar",
                   "--archetype", "windows", "--personality", "generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Archetype windows is not compileable.", command)

    def test_120_add_existing_leaf_path(self):
        action = "testaction"
        path = "actions/%s/user" % action
        command = ADD_CMD + ["--path", path, "--value", "user1"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=%s already exists"
                         % path, command)

    def test_130_update_existing_leaf_path(self):
        action = "testaction"
        path = "actions/%s/user" % action
        command = UPD_CMD + ["--path", path, "--value", "user2"]
        self.noouttest(command)

        out = self.commandtest(SHOW_CMD)
        expected = 'actions: { "%s": { "command": "/bin/%s", "user": "user2" } }' % (action, action)
        self.check_match(out, expected, SHOW_CMD)

    def test_150_add_testaction2(self):
        action = "testaction2"
        path = "actions/%s" % action
        value = '{ "command": "/bin/%s", "timeout": 100, "user": "user1" }' % action
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        out = self.commandtest(SHOW_CMD)
        self.check_match(out, value, SHOW_CMD)

    def test_160_add_existing_json_path(self):
        action = "testaction2"
        path = "actions/%s" % action
        value = '{ "command": "/bin/%s", "user": "user1", "timeout": 100 }' % action
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=actions/testaction2 already exists", command)

    def test_170_upd_nonexisting_leaf_path(self):
        action = "testaction"
        path = "actions/%s/badpath" % action
        command = UPD_CMD + ["--path", path, "--value", "badvalue"]
        err = self.notfoundtest(command)
        self.matchoutput(err, "No parameter of path=%s defined." % path, command)

    def test_180_add_disallowed_leaf_path(self):
        action = "testaction"
        path = "actions/%s/badpath" % action
        value = 800
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Additional properties are not allowed", command)

    def test_190_add_metric(self):
        command = ADD_CMD + ["--path", "monitoring/metric",
                             "--value", json.dumps(test_metric)]
        self.noouttest(command)

    def test_200_add_path(self):
        path = "espinfo/function"
        value = "crash"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "espinfo/users"
        value = "someusers, otherusers"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "espinfo/class"
        value = "INFRASTRUCTURE"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.successtest(command)

    def test_210_add_existing_path(self):
        path = "espinfo/function"
        value = "crash"
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=%s already exists" % path, command)

    def test_220_upd_existing_path(self):
        path = "espinfo/function"
        value = "production"
        command = UPD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

    def test_230_upd_nonexisting_path(self):
        path = "espinfo/badpath"
        value = "somevalue"
        command = UPD_CMD + ["--path", path, "--value", value]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

    def test_240_verify_path(self):
        out = self.commandtest(SHOW_CMD)
        self.check_match(out,
                         'espinfo: { '
                         '"class": "INFRASTRUCTURE", '
                         '"function": "production", '
                         '"users": [ "someusers", "otherusers" ] }',
                         SHOW_CMD)
        self.check_match(out, '"testaction": { "command": "/bin/testaction", "user": "user2" }', SHOW_CMD)
        self.check_match(out, '"testaction2": { "command": "/bin/testaction2", "timeout": 100, "user": "user1" } }', SHOW_CMD)

    def test_245_verify_path_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        parameters = self.protobuftest(cmd, expect=5)

        params = {}
        for param in parameters:
            params[param.path] = param.value

        self.assertIn('espinfo/function', params)
        self.assertEqual(params['espinfo/function'], 'production')

        self.assertIn('espinfo/class', params)
        self.assertEqual(params['espinfo/class'], 'INFRASTRUCTURE')

        self.assertIn('espinfo/users', params)
        self.assertEqual(params['espinfo/users'], 'someusers,otherusers')

        self.assertIn('actions', params)
        self.assertEqual(json.loads(params['actions']), {
            "testaction": {
                "command": "/bin/testaction",
                "user": "user2"
            },
            "testaction2": {
                "command": "/bin/testaction2",
                "user": "user1",
                "timeout": 100
            }
        })

        self.assertIn('monitoring/metric', params)
        self.assertEqual(json.loads(params['monitoring/metric']), test_metric)

    def test_250_verify_actions(self):
        ACT_CAT_CMD = CAT_CMD + ["--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        match_str1 = r'"testaction" = nlist\(\s*"command", "/bin/testaction",\s*"user", "user2"\s*\)'
        match_str2 = r'"testaction2" = nlist\(\s*"command", "/bin/testaction2",\s*"timeout", 100,\s*"user", "user1"\s*\)\s*'

        self.searchoutput(out, match_str1, ACT_CAT_CMD)
        self.searchoutput(out, match_str2, ACT_CAT_CMD)

    def test_255_verify_espinfo(self):
        ESP_CAT_CMD = CAT_CMD + ["--param_tmpl=espinfo"]
        out = self.commandtest(ESP_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev\+next/espinfo;\s*'
                               r'"class" = "INFRASTRUCTURE";\s*'
                               r'"function" = "production";\s*'
                               r'"users" = list\(\s*'
                               r'"someusers",\s*'
                               r'"otherusers"\s*'
                               r'\);',
                          ESP_CAT_CMD)

    def test_260_verify_monitoring(self):
        command = CAT_CMD + ["--param_tmpl", "monitoring"]
        out = self.commandtest(command)
        # Check the formatting of the floating point value
        self.searchoutput(out, r'"maxdiff", 3\.0+,', command)

    def test_300_validate(self):
        out = self.badrequesttest(VAL_CMD)
        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: testrequired \[required\]\s*'
                          r'Type: string\s*'
                          r'Template: foo',
                          VAL_CMD)

    def test_305_promote(self):
        self.noouttest(["promote", "--personality", PERSONALITY,
                        "--archetype", "aquilon"])

    def test_310_reconfigurehost(self):
        path = "espinfo/function"
        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

        command = ["reconfigure", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--personality", PERSONALITY, "--personality_stage", "next"]
        (out, err) = self.failuretest(command, 4)
        self.matchoutput(err, "'/system/personality/function' does not have an associated value", command)
        self.matchoutput(err, "BUILD FAILED", command)

    def test_315_verify_stage_diff(self):
        # The parameter should still be present in 'current'
        command = ["show_parameter", "--personality", PERSONALITY,
                   "--archetype", "aquilon", "--personality_stage", "current"]
        out = self.commandtest(command)
        self.matchoutput(out, '"function": "production"', command)

        command = ["show_parameter", "--personality", PERSONALITY,
                   "--archetype", "aquilon", "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchclean(out, '"function": "production"', command)

    def test_320_add_all_required(self):
        path = "testrequired"
        value = "set"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "espinfo/function"
        value = "crash"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

    def test_325_validate_all_required(self):
        # Validate a personality that has no parameters defined
        out, err = self.successtest(VAL_CMD)
        self.assertEmptyOut(out, VAL_CMD)
        self.matchoutput(err, "All required parameters specified.", VAL_CMD)

    def test_330_reconfigurehost(self):
        command = ["reconfigure", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--personality", PERSONALITY, "--personality_stage", "next"]
        self.successtest(command)

    def test_400_add_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "almostready"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = ADD_CMD + ["--path", path, "--value=test", ]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_400_validate_modifying_other_params_works(self):
        path = "espinfo/function"
        value = "production"
        command = UPD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "espinfo/description"
        value = "add other params in host ready state"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

    def test_405_add_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = ADD_CMD + ["--path", path, "--value=test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_410_add_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = ADD_CMD + ["--path", path, "--value=test"]
        self.successtest(command)

    def test_420_upd_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = UPD_CMD + ["--path", path, "--value=test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_430_upd_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = UPD_CMD + ["--path", path, "--value=test"]
        self.successtest(command)

    def test_440_del_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = DEL_CMD + ["--path", path]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test_rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_450_del_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test_rebuild_required"
        command = DEL_CMD + ["--path", path]
        self.successtest(command)

    def test_500_verify_diff(self):
        cmd = ["show_diff", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--personality_stage", "next", "--other", OTHER_PERSONALITY]

        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Differences for Parameters:\s*'
                          r'missing Parameters in Personality aquilon/utpers-dev@current:\s*'
                          r'//actions/testaction/command\s*'
                          r'//actions/testaction/user\s*'
                          r'//actions/testaction2/command\s*'
                          r'//actions/testaction2/timeout\s*'
                          r'//actions/testaction2/user\s*'
                          r'//espinfo/users/1\s*'
                          r'//monitoring/metric/_20003/active\s*'
                          r'//monitoring/metric/_20003/class\s*'
                          r'//monitoring/metric/_20003/descr\s*'
                          r'//monitoring/metric/_20003/latestonly\s*'
                          r'//monitoring/metric/_20003/name\s*'
                          r'//monitoring/metric/_20003/period\s*'
                          r'//monitoring/metric/_20003/smooth/maxdiff\s*'
                          r'//monitoring/metric/_20003/smooth/maxtime\s*'
                          r'//monitoring/metric/_20003/smooth/typeString\s*'
                          r'//testrequired\s*'
                          r'matching Parameters with different values:\s*'
                          r'//espinfo/function value=production, othervalue=development\s*'
                          r'//espinfo/users/0 value=someusers, othervalue=IT / TECHNOLOGY',
                          cmd)

    def test_520_copy_from(self):
        cmd = ["add_personality", "--archetype", ARCHETYPE, "--personality", "myshinynew",
               "--copy_from", PERSONALITY, "--copy_stage", "next"]
        self.successtest(cmd)

        cmd = ["show_diff", "--archetype", ARCHETYPE,
               "--personality", PERSONALITY, "--personality_stage", "next",
               "--other", "myshinynew", "--other_stage", "next"]
        out = self.noouttest(cmd)

        cmd = ["del_personality", "--archetype", ARCHETYPE, "--personality", "myshinynew"]
        self.successtest(cmd)

    def test_530_search_parameter(self):
        cmd = ["search_parameter", "--archetype", ARCHETYPE, "--path", "espinfo/function"]
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
                          r'Host Personality: testpersona/dev Archetype: aquilon\s*'
                          r'Stage: next\s*'
                          r'espinfo/function: "production"',
                          cmd)
        self.searchoutput(out,
                          r'Host Personality: utpers-dev Archetype: aquilon\s*'
                          r'Stage: current\s*'
                          r'espinfo/function: "development"',
                          cmd)

    def test_535_search_parameter(self):
        cmd = ["search_parameter", "--archetype", ARCHETYPE, "--path", "actions"]
        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Host Personality: testpersona/dev Archetype: aquilon\s*'
                          r'Stage: next\s*'
                          r'actions: {\s*'
                          r'"testaction": {\s*"command": "/bin/testaction",\s*"user": "user2"\s*},\s*'
                          r'"testaction2": {\s*"command": "/bin/testaction2",\s*"timeout": 100,\s*"user": "user1"\s*}\s*}',
                          cmd)

    def test_550_verify_actions(self):
        ACT_CAT_CMD = CAT_CMD + ["--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        match_str1 = r'"testaction" = nlist\(\s*"command", "/bin/testaction",\s*"user", "user2"\s*\)'
        match_str2 = r'"testaction2" = nlist\(\s*"command", "/bin/testaction2",\s*"timeout", 100,\s*"user", "user1"\s*\)\s*'

        self.searchoutput(out, match_str1, ACT_CAT_CMD)
        self.searchoutput(out, match_str2, ACT_CAT_CMD)

    def test_555_verify_espinfo(self):
        ESP_CAT_CMD = CAT_CMD + ["--param_tmpl=espinfo"]
        out = self.commandtest(ESP_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev\+next/espinfo;\s*', ESP_CAT_CMD)
        self.searchoutput(out, r'"function" = "production";', ESP_CAT_CMD)
        self.searchoutput(out, r'"class" = "INFRASTRUCTURE";', ESP_CAT_CMD)
        self.searchoutput(out, r'"users" = list\(\s*"someusers",\s*"otherusers"\s*\);', ESP_CAT_CMD)

    def test_555_verify_defaults(self):
        cmd = CAT_CMD + ["--param_tmpl=foo"]
        out = self.commandtest(cmd)
        self.matchoutput(out,
                         'structure template personality/testpersona/dev+next/foo;',
                         cmd)
        self.matchoutput(out, '"testboolean" = true;', cmd)
        self.matchoutput(out, '"testfalsedefault" = false;', cmd)
        self.matchoutput(out, '"testfloat" = 100.100;', cmd)
        self.matchoutput(out, '"testint" = 60;', cmd)
        self.matchoutput(out, '"teststring" = "default";', cmd)
        self.matchoutput(out, '"testrequired" = "set";', cmd)
        # TODO: get_path_under_top() makes the value come out not quite as
        # expected - the "testjson" prefix is missing
        self.searchoutput(out,
                          r'"key" = "param_key";\s*'
                          r'"values" = list\(\s*0\s*\);\s*',
                          cmd)
        self.searchoutput(out,
                          r'"testlist" = list\(\s*"val1",\s*"val2"\s*\);',
                          cmd)

    def test_560_verify_default(self):
        # included by default
        SEC_CAT_CMD = CAT_CMD + ["--param_tmpl=windows"]
        out = self.commandtest(SEC_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev\+next/windows;\s*'
                               r'"windows" = list\(\s*nlist\(\s*"day", "Sun",\s*"duration", 8,\s*"start", "08:00"\s*\)\s*\);',
                          SEC_CAT_CMD)

    def test_600_del_path(self):
        action = "testaction"
        path = "actions/%s/user" % action
        command = DEL_CMD + ["--path", path]
        err = self.badrequesttest(command)
        self.matchoutput(err, "'user' is a required property", command)

        path = "actions/" + action
        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

    def test_610_del_path_notfound(self):
        path = "boo"
        command = DEL_CMD + ["--path", path]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions." % path,
                         command)

    def test_620_del_path_json(self):
        command = DEL_CMD + ["--path", "actions"]
        self.noouttest(command)

    def test_630_verify_show(self):
        out = self.commandtest(SHOW_CMD)
        self.check_match_clean(out, 'testaction', SHOW_CMD)
        self.check_match_clean(out, 'testaction2', SHOW_CMD)

    def test_640_verify_actions(self):
        # cat commands
        ACT_CAT_CMD = CAT_CMD + ["--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        self.searchclean(out, "testaction", ACT_CAT_CMD)
        self.searchclean(out, "testaction2", ACT_CAT_CMD)

    def test_660_verify_default(self):
        # included by default
        SEC_CAT_CMD = CAT_CMD + ["--param_tmpl=windows"]
        out = self.commandtest(SEC_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev\+next/windows;\s*'
                               r'"windows" = list\(\s*nlist\(\s*"day", "Sun",\s*"duration", 8,\s*"start", "08:00"\s*\)\s*\);',
                          SEC_CAT_CMD)

    def test_700_missing_stage(self):
        command = ["add_parameter", "--personality", "nostage",
                   "--archetype", "aquilon",
                   "--path", "espinfo/function", "--value", "foobar",
                   "--personality_stage", "previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality aquilon/nostage does not have "
                         "stage previous.", command)

    def test_700_bad_stage(self):
        command = ["add_parameter", "--personality", "nostage",
                   "--archetype", "aquilon",
                   "--path", "espinfo/function", "--value", "foobar",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

    def test_999_cleanup(self):
        """ cleanup of all data created here """

        command = ["reconfigure", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        self.successtest(command)

        cmd = ["del_personality", "--archetype", ARCHETYPE, "--personality", PERSONALITY]
        self.noouttest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameter)
    unittest.TextTestRunner(verbosity=2).run(suite)
