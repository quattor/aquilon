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
"""Module for testing parameter support."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand

PERSONALITY = 'testpersona/dev'

ARCHETYPE = 'aquilon'
OTHER_PERSONALITY = 'eaitools'


SHOW_CMD = ["show", "parameter", "--personality", PERSONALITY]

ADD_CMD = ["add", "parameter", "--personality", PERSONALITY]

UPD_CMD = ["update", "parameter", "--personality", PERSONALITY]

DEL_CMD = ["del", "parameter", "--personality", PERSONALITY]

CAT_CMD = ["cat", "--personality", PERSONALITY]

VAL_CMD = ["validate_parameter", "--personality", PERSONALITY]


class TestParameter(TestBrokerCommand):

    def check_match(self, out, expected, command):
        out = ' '.join(out.split())
        self.matchoutput(out, expected, command)

    def check_match_clean(self, out, expected, command):
        out = ' '.join(out.split())
        self.matchclean(out, expected, command)

    def test_000_verify_preload(self):

        cmd = ["add_personality", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--eon_id=2", "--host_environment=dev", "--comment", "tests parameters"]
        self.noouttest(cmd)

        err = self.notfoundtest(SHOW_CMD)
        self.matchoutput(err,
                         "No parameters found for personality %s." % PERSONALITY, SHOW_CMD)

    def test_100_add_re_path(self):
        action = "testaction"
        path = "action/%s/user" % action
        command = ADD_CMD + ["--path", path, "--value", "user1"]
        self.noouttest(command)

        path = "action/%s/command" % action
        command = ADD_CMD + ["--path", path, "--value", "/bin/%s" % action]
        self.noouttest(command)

    def test_100_add_noncompileable(self):
        command = ["add", "parameter", "--path", "foo", "--value", "bar",
                   "--archetype", "windows", "--personality", "generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Archetype windows is not compileable.", command)

    def test_120_add_existing_re_path(self):
        action = "testaction"
        path = "action/%s/user" % action
        command = ADD_CMD + ["--path", path, "--value", "user1"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=%s already exists"
                         % path, command)

    def test_130_verify_re(self):
        action = "testaction"
        out = self.commandtest(SHOW_CMD)
        expected = 'action: { "%s": { "command": "/bin/%s", "user": "user1" } }' % (action, action)
        self.check_match(out, expected, SHOW_CMD)

    def test_132_verify_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 1)
        params = p.parameters

        self.failUnlessEqual(params[0].path, 'action')
        self.failUnlessEqual(params[0].value, '{"testaction": {"command": "/bin/testaction", "user": "user1"}}')

    def test_140_update_existing_re_path(self):
        action = "testaction"
        path = "action/%s/user" % action
        command = UPD_CMD + ["--path", path, "--value", "user2"]
        self.noouttest(command)

        out = self.commandtest(SHOW_CMD)
        expected = 'action: { "%s": { "command": "/bin/%s", "user": "user2" } }' % (action, action)
        self.check_match(out, expected, SHOW_CMD)

    def test_150_add_re_json_path(self):
        action = "testaction2"
        path = "action/%s" % action
        value = '{ "command": "/bin/%s", "user": "user1", "timeout": 100 }' % action
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        out = self.commandtest(SHOW_CMD)
        self.check_match(out, value, SHOW_CMD)

    def test_160_add_existing_re_json_path(self):
        action = "testaction2"
        path = "action/%s" % action
        value = '{ "command": "/bin/%s", "user": "user1", "timeout": 100 }' % action
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=action/testaction2 already exists", command)

    def test_170_upd_nonexisting_re_path(self):
        action = "testaction"
        path = "action/%s/badpath" % action
        command = UPD_CMD + ["--path", path, "--value", "badvalue"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

    def test_180_add_nonexisting_re_path(self):
        action = "testaction"
        path = "actions/%s/badpath" % action
        value = 800
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

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
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

    def test_240_verify_path(self):
        out = self.commandtest(SHOW_CMD)
        self.check_match(out,
                         'espinfo: { "function": "production", '
                         '"users": "someusers, otherusers", '
                         '"class": "INFRASTRUCTURE" }', SHOW_CMD)
        self.check_match(out, '"testaction": { "command": "/bin/testaction", "user": "user2" }', SHOW_CMD)
        self.check_match(out, '"testaction2": { "command": "/bin/testaction2", "user": "user1", "timeout": 100 } }', SHOW_CMD)

    def test_245_verify_path_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 4)
        params = p.parameters

        self.failUnlessEqual(params[0].path, 'espinfo/function')
        self.failUnlessEqual(params[0].value, 'production')

        self.failUnlessEqual(params[1].path, 'espinfo/class')
        self.failUnlessEqual(params[1].value, 'INFRASTRUCTURE')

        self.failUnlessEqual(params[2].path, 'espinfo/users')
        self.failUnlessEqual(params[2].value, 'someusers, otherusers')

        self.failUnlessEqual(params[3].path, 'action')
        self.failUnlessEqual(params[3].value, u'{"testaction": {"command": "/bin/testaction", "user": "user2"}, "testaction2": {"command": "/bin/testaction2", "user": "user1", "timeout": 100}}')

    def test_250_verify_actions(self):
        ACT_CAT_CMD = CAT_CMD + ["--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        match_str1 = '"testaction" = nlist\(\s*"command", "/bin/testaction",\s*"user", "user2"\s*\)'
        match_str2 = '"testaction2" = nlist\(\s*"command", "/bin/testaction2",\s*"timeout", 100,\s*"user", "user1"\s*\)\s*'

        self.searchoutput(out, match_str1, ACT_CAT_CMD)
        self.searchoutput(out, match_str2, ACT_CAT_CMD)

    def test_255_verify_espinfo(self):
        ESP_CAT_CMD = CAT_CMD + ["--param_tmpl=espinfo"]
        out = self.commandtest(ESP_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev/espinfo;\s*'
                               r'"function" = "production";\s*'
                               r'"class" = "INFRASTRUCTURE";\s*'
                               r'"users" = list\(\s*'
                               r'"someusers",\s*'
                               r'"otherusers"\s*'
                               r'\);',
                          ESP_CAT_CMD)

    def test_300_validate(self):
        out = self.badrequesttest(VAL_CMD)
        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: espinfo/threshold \[required\]\s*'
                          r'Type: int\s*'
                          r'Template: espinfo',
                          VAL_CMD)

    def test_310_reconfigurehost(self):
        path = "espinfo/function"
        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

        command = ["reconfigure", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--personality", PERSONALITY]
        (out, err) = self.failuretest(command, 4)
        self.matchoutput(err, "'/system/personality/function' does not have an associated value", command)
        self.matchoutput(err, "BUILD FAILED", command)


    def test_320_add_all_required(self):
        path = "espinfo/threshold"
        value = 0
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
                   "--personality", PERSONALITY]
        self.successtest(command)

    def test_400_add_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "almostready"]
        self.successtest(command)

        path = "test/rebuild_required"
        command = ADD_CMD + ["--path", path, "--value=test", ]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
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

        path = "test/rebuild_required"
        command = ADD_CMD + ["--path", path, "--value=test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_410_add_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test/rebuild_required"
        command = ADD_CMD + ["--path", path, "--value=test"]
        self.successtest(command)

    def test_420_upd_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test/rebuild_required"
        command = UPD_CMD + ["--path", path, "--value=test"]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_430_upd_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test/rebuild_required"
        command = UPD_CMD + ["--path", path, "--value=test"]
        self.successtest(command)

    def test_440_del_rebuild_required_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test/rebuild_required"
        command = DEL_CMD + ["--path", path]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_450_del_rebuild_required_non_ready(self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test/rebuild_required"
        command = DEL_CMD + ["--path", path]
        self.successtest(command)

    def test_500_verify_diff(self):
        cmd = ["show_diff", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--other", OTHER_PERSONALITY]

        out = self.commandtest(cmd)
        self.searchoutput(out, r'Differences for Parameters:\s*'
                               r'missing Parameters in Personality aquilon/eaitools:\s*'
                               r'//action/testaction/command\s*'
                               r'//action/testaction/user\s*'
                               r'//action/testaction2/command\s*'
                               r'//action/testaction2/timeout\s*'
                               r'//action/testaction2/user\s*'
                               r'matching Parameters with different values:\s*'
                               r'//espinfo/function value=production, othervalue=development\s*'
                               r'//espinfo/users value=someusers, otherusers, othervalue=IT / TECHNOLOGY',
                         cmd)

    def test_520_copy_from(self):
        cmd = ["add_personality", "--archetype", ARCHETYPE, "--personality", "myshinynew",
                "--eon_id=2", "--copy_from", PERSONALITY, "--host_environment", "dev"]
        self.successtest(cmd)

        cmd = ["show_diff", "--archetype", ARCHETYPE, "--personality", PERSONALITY,
               "--other", "myshinynew"]
        out = self.noouttest(cmd)

        cmd = ["del_personality", "--archetype", ARCHETYPE, "--personality", "myshinynew"]
        self.successtest(cmd)

    def test_530_search_parameter(self):
        cmd = ["search_parameter", "--archetype", ARCHETYPE, "--path", "espinfo/function" ]
        out = self.commandtest(cmd)
        self.searchoutput(out,'Personality aquilon/compileserver:\s*espinfo/function: "development"', cmd)
        self.searchoutput(out,'Personality aquilon/inventory:\s*espinfo/function: "development"', cmd)
        self.searchoutput(out,'Personality aquilon/unixeng-test:\s*espinfo/function: "development"', cmd)
        self.searchoutput(out,'Personality aquilon/testpersona/dev:\s*espinfo/function: "production"', cmd)
        self.searchoutput(out,'Personality aquilon/eaitools:\s*espinfo/function: "development"', cmd)
 

    def test_535_search_parameter(self):
        cmd = ["search_parameter", "--archetype", ARCHETYPE, "--path", "action" ]
        out = self.commandtest(cmd)
        self.searchoutput(out, r'Personality aquilon/testpersona/dev:\s*'
                               r'action: {"testaction": {"command": "/bin/testaction", "user": "user2"}, '
                               r'"testaction2": {"command": "/bin/testaction2", "user": "user1", "timeout": 100}}', cmd)

    def test_550_verify_actions(self):
        ACT_CAT_CMD = CAT_CMD + ["--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        match_str1 = '"testaction" = nlist\(\s*"command", "/bin/testaction",\s*"user", "user2"\s*\)'
        match_str2 = '"testaction2" = nlist\(\s*"command", "/bin/testaction2",\s*"timeout", 100,\s*"user", "user1"\s*\)\s*'

        self.searchoutput(out, match_str1, ACT_CAT_CMD)
        self.searchoutput(out, match_str2, ACT_CAT_CMD)

    def test_555_verify_espinfo(self):
        ESP_CAT_CMD = CAT_CMD + ["--param_tmpl=espinfo"]
        out = self.commandtest(ESP_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev/espinfo;\s*', ESP_CAT_CMD)
        self.searchoutput(out, r'"function" = "production";', ESP_CAT_CMD)
        self.searchoutput(out, r'"threshold" = 0;', ESP_CAT_CMD)
        self.searchoutput(out, r'"class" = "INFRASTRUCTURE";', ESP_CAT_CMD)
        self.searchoutput(out, r'"users" = list\(\s*"someusers",\s*"otherusers"\s*\);', ESP_CAT_CMD)

    def test_560_verify_default(self):
        ##included by default
        SEC_CAT_CMD = CAT_CMD + ["--param_tmpl=windows"]
        out = self.commandtest(SEC_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev/windows;\s*'
                               r'"windows" = list\(\s*nlist\(\s*"day", "Sun",\s*"duration", 8,\s*"start", "08:00"\s*\)\s*\);',
                          SEC_CAT_CMD)

    def test_600_del_path(self):
        action = "testaction"
        path = "action/%s/user" % action
        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

        path = "action/%s/command" % action
        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

    def test_610_del_path_notfound(self):
        path = "boo"
        command = DEL_CMD + ["--path", path]
        err = self.notfoundtest(command)
        self.matchoutput(err, "No parameter of path=%s defined" % path, command)

    def test_620_del_path_json(self):
        action = "testaction2"
        path = "action/%s" % action
        command = DEL_CMD + ["--path", path]
        err = self.noouttest(command)

        path = "espinfo/"
        command = DEL_CMD + ["--path", path]
        err = self.noouttest(command)

    def test_630_verify_show(self):
        out = self.commandtest(SHOW_CMD)
        self.check_match_clean(out, 'testaction', SHOW_CMD)
        self.check_match_clean(out, 'testaction2', SHOW_CMD)

    def test_640_verify_actions(self):
        ## cat commands
        ACT_CAT_CMD = CAT_CMD + ["--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        self.searchclean(out, "testaction", ACT_CAT_CMD)
        self.searchclean(out, "testaction2", ACT_CAT_CMD)

    def test_650_verify_esp(self):
        ESP_CAT_CMD = CAT_CMD + ["--param_tmpl=espinfo"]
        err = self.commandtest(ESP_CAT_CMD)
        self.searchclean(err, r'"function" = "production";', ESP_CAT_CMD)

    def test_660_verify_default(self):
        ##included by default
        SEC_CAT_CMD = CAT_CMD + ["--param_tmpl=windows"]
        out = self.commandtest(SEC_CAT_CMD)
        self.searchoutput(out, r'structure template personality/testpersona/dev/windows;\s*'
                               r'"windows" = list\(\s*nlist\(\s*"day", "Sun",\s*"duration", 8,\s*"start", "08:00"\s*\)\s*\);',
                          SEC_CAT_CMD)

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
