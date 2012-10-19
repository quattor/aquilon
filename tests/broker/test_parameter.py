#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing parameter support."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand

PERSONALITY = 'testpersona/dev'

ARCHETYPE = 'aquilon'
OTHER_PERSONALITY = 'eaitools'

## validation parameters by templates
PARAM_DEFS = {
"access": [
    { "path": "access/netgroup", "value_type": "list",  "description": "netgroups access" },
    { "path": "access/users",    "value_type": "list",  "description": "users access"},
],
"actions": [
    { "path": "action/\w+/user", "value_type": "string", "description": "action user" },
    { "path": "action/\w+/command", "value_type": "string", "description": "action command" },
    { "path": "action/\w+",      "value_type": "json",   "description": "per action block" },
    { "path": "action",          "value_type": "json",   "description": "per action block" },
],
"startup": [
    { "path": "startup/actions",  "value_type": "list", "description": "startup actions" },
],
"shutdown": [
    { "path": "shutdown/actions", "value_type": "list", "description": "shutdown actions" },
],
"maintenance": [
    { "path": "maintenance/actions", "value_type": "list", "description": "maintenance actions" },
],
"monitoring": [
    { "path": "monitoring/alert", "value_type": "json", "description": "monitoring " },
],
"espinfo": [
    { "path": "esp/function", "value_type": "string", "description": "espinfo function", "required": True },
    { "path": "esp/class",    "value_type": "string", "description": "espinfo class", "required": True },
    { "path": "esp/users",    "value_type": "list", "description": "espinfo users", "required": True },
    { "path": "esp/threshold", "value_type": "int", "description": "espinfo threshold", "required": True },
    { "path": "esp/description", "value_type": "string", "description": "espinfo desc" },
],
"windows": [
    { "path": "windows/windows", "value_type": "json" , "required": True, "default": '[{"duration": 8, "start": "08:00", "day": "Sun"}]' }
],
"testrebuild": [
    { "path" : "test/rebuild_required", "value_type": "string", "rebuild_required": True }
],
}

SHOW_CMD = ["show", "parameter", "--personality", PERSONALITY ]

ADD_CMD = ["add", "parameter", "--personality", PERSONALITY]

UPD_CMD = ["update", "parameter", "--personality", PERSONALITY]

DEL_CMD = ["del", "parameter", "--personality", PERSONALITY]

CAT_CMD = ["cat", "--personality", PERSONALITY ]

VAL_CMD = ["validate_parameter", "--personality", PERSONALITY ]

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
                         "No parameters found for personality %s." % PERSONALITY,  SHOW_CMD)

        for template in PARAM_DEFS:
            paths = PARAM_DEFS[template]
            for p in paths:
                cmd = ["add_parameter_definition", "--archetype=aquilon",
                       "--path", p["path"], "--template", template,
                       "--value_type", p["value_type"]]
                if "required" in p:
                    cmd.append( "--required" )
                if "rebuild_required" in p:
                    cmd.append( "--rebuild_required" )
                if "default" in p:
                    cmd.extend(["--default", p["default"]])

                self.noouttest(cmd)


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
                         %  path, command)

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
        command = UPD_CMD + [ "--path", path, "--value", "user2"]
        self.noouttest(command)

        out = self.commandtest(SHOW_CMD)
        expected = 'action: { "%s": { "command": "/bin/%s", "user": "user2" } }' % (action, action)
        self.check_match(out, expected, SHOW_CMD)

    def test_150_add_re_json_path(self):
        action = "testaction2"
        path = "action/%s" % action
        value  = '{ "command": "/bin/%s", "user": "user1", "timeout": 100 }' % action
        command = ADD_CMD + ["--path", path, "--value", value ]
        self.noouttest(command)

        out = self.commandtest(SHOW_CMD)
        self.check_match(out, value, SHOW_CMD)

    def test_160_add_existing_re_json_path(self):
        action = "testaction2"
        path = "action/%s" % action
        value  = '{ "command": "/bin/%s", "user": "user1", "timeout": 100 }' % action
        command = ADD_CMD + ["--path", path, "--value", value ]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=action/testaction2 already exists", command)

    def test_170_upd_nonexisting_re_path(self):
        action = "testaction"
        path = "action/%s/badpath" % action
        command = UPD_CMD + [ "--path", path, "--value", "badvalue"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

    def test_180_add_nonexisting_re_path(self):
        action = "testaction"
        path = "actions/%s/badpath" % action
        value = 800
        command = ADD_CMD + [ "--path", path, "--value", value ]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

    def test_200_add_path(self):
        path = "esp/function"
        value = "crash"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "esp/users"
        value = "someusers, otherusers"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "esp/class"
        value = "INFRASTRUCTURE"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.successtest(command)

    def test_210_add_existing_path(self):
        path = "esp/function"
        value = "crash"
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Parameter with path=%s already exists" % path, command)

    def test_220_upd_existing_path(self):
        path = "esp/function"
        value = "development"
        command = UPD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

    def test_230_upd_nonexisting_path(self):
        path = "esp/badpath"
        value = "somevalue"
        command = UPD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Parameter %s does not match any parameter definitions" % path, command)

    def test_240_verify_path(self):
        out = self.commandtest(SHOW_CMD)
        self.check_match(out,
                         'esp: { "function": "development", '
                         '"users": "someusers, otherusers", '
                         '"class": "INFRASTRUCTURE" }', SHOW_CMD)
        self.check_match(out, '"testaction": { "command": "/bin/testaction", "user": "user2" }', SHOW_CMD)
        self.check_match(out, '"testaction2": { "command": "/bin/testaction2", "user": "user1", "timeout": 100 } }', SHOW_CMD)

    def test_245_verify_path_proto(self):
        cmd = SHOW_CMD + ["--format=proto"]
        out = self.commandtest(cmd)
        p = self.parse_parameters_msg(out, 4)
        params = p.parameters

        self.failUnlessEqual(params[0].path, 'esp/function')
        self.failUnlessEqual(params[0].value, 'development')

        self.failUnlessEqual(params[1].path, 'esp/class')
        self.failUnlessEqual(params[1].value, 'INFRASTRUCTURE')

        self.failUnlessEqual(params[2].path, 'esp/users')
        self.failUnlessEqual(params[2].value, 'someusers')

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
                               r'"function" = "development";\s*'
                               r'"class" = "INFRASTRUCTURE";\s*'
                               r'"users" = list\(\s*'
                               r'"someusers",\s*'
                               r'"otherusers"\s*'
                               r'\);',
                          ESP_CAT_CMD)

    def test_300_validate_noparams(self):
        # Validate a personality that has no parameters defined
        command = ["validate", "parameter", "--personality", "utpersonality/dev"]
        out, err = self.successtest(command)
        self.assertEmptyOut(out, command)
        self.matchoutput(err, "All required parameters specified.", command)

    def test_300_validate(self):
        out = self.badrequesttest(VAL_CMD)
        self.searchoutput(out,
                          r'Following required parameters have not been specified:\s*'
                          r'Parameter Definition: esp/threshold \[required\]\s*'
                          r'Type: int\s*'
                          r'Template: espinfo',
                          VAL_CMD)

    def test_310_reconfigurehost(self):
        command = ["reconfigure", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--personality", PERSONALITY]
        (out, err) = self.failuretest(command, 4)
        self.matchoutput (err, "record is missing required field: threshold", command)
        self.matchoutput (err, "BUILD FAILED", command)

    def test_320_add_all_required(self):
        path = "esp/threshold"
        value = 0
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

    def test_400_add_rebuild_required_ready (self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "almostready"]
        self.successtest(command)

        path = "test/rebuild_required"
        value = "test"
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_400_validate_modifying_other_params_works (self):
        path = "esp/function"
        value = "development"
        command = UPD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        path = "esp/description"
        value = "add other params in host ready state"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.noouttest(command)

        command = DEL_CMD + ["--path", path]
        self.noouttest(command)

    def test_405_add_rebuild_required_ready (self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test/rebuild_required"
        value = "test"
        command = ADD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_410_add_rebuild_required_non_ready (self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test/rebuild_required"
        value = "test"
        command = ADD_CMD + ["--path", path, "--value", value]
        self.successtest(command)

    def test_420_upd_rebuild_required_ready (self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "ready"]
        self.successtest(command)

        path = "test/rebuild_required"
        value = "test"
        command = UPD_CMD + ["--path", path, "--value", value]
        err = self.badrequesttest(command)
        self.searchoutput(err,
                          r'Modifying parameter test/rebuild_required value needs a host rebuild. '
                          r'There are hosts associated to the personality in non-ready state. '
                          r'Please set these host to status of rebuild to continue.',
                          command)

    def test_430_upd_rebuild_required_non_ready (self):
        command = ["change_status", "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--buildstatus", "rebuild"]
        self.successtest(command)

        path = "test/rebuild_required"
        value = "test"
        command = UPD_CMD + ["--path", path, "--value", value]
        self.successtest(command)

    def test_440_del_rebuild_required_ready (self):
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

    def test_450_del_rebuild_required_non_ready (self):
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
        self.searchoutput (out, r'Differences for Parameters:\s*'
                               r'missing Parameters in Personality aquilon/eaitools:\s*'
                               r'//action/testaction/command\s*'
                               r'//action/testaction/user\s*'
                               r'//action/testaction2/command\s*'
                               r'//action/testaction2/timeout\s*'
                               r'//action/testaction2/user\s*'
                               r'//esp/class\s*'
                               r'//esp/function\s*'
                               r'//esp/threshold\s*'
                               r'//esp/users',
                         cmd)

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
        self.searchoutput(out, r'"function" = "development";', ESP_CAT_CMD)
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
        command = DEL_CMD + ["--path", path ]
        self.noouttest(command)

    def test_610_del_path_notfound(self):
        path = "boo"
        command =  DEL_CMD + ["--path", path]
        err = self.notfoundtest(command)
        self.matchoutput(err, "No parameter of path=%s defined" % path, command)

    def test_620_del_path_json(self):
        action = "testaction2"
        path = "action/%s" % action
        command =  DEL_CMD + ["--path", path]
        err = self.noouttest(command)

        path = "esp"
        command =  DEL_CMD + ["--path", path]
        err = self.noouttest(command)

    def test_630_verify_show(self):
        out = self.commandtest(SHOW_CMD)
        self.check_match_clean(out, 'testaction', SHOW_CMD)
        self.check_match_clean(out, 'testaction2', SHOW_CMD)

    def test_640_verify_actions(self):
        ## cat commands
        ACT_CAT_CMD =  CAT_CMD + [ "--param_tmpl=actions"]
        out = self.commandtest(ACT_CAT_CMD)

        self.searchclean(out, "testaction", ACT_CAT_CMD)
        self.searchclean(out, "testaction2", ACT_CAT_CMD)

    def test_650_verify_esp(self):
        ESP_CAT_CMD =  CAT_CMD + [ "--param_tmpl=espinfo"]
        err = self.commandtest(ESP_CAT_CMD)
        self.searchclean(err, r'"function" = "development";', ESP_CAT_CMD)

    def test_660_verify_default(self):
        ##included by default
        SEC_CAT_CMD =  CAT_CMD + [ "--param_tmpl=windows"]
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

        for template in PARAM_DEFS:
            paths = PARAM_DEFS[template]
            for p in paths:
                cmd = ["del_parameter_definition", "--archetype=aquilon", "--path", p["path"]]
                self.noouttest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameter)
    unittest.TextTestRunner(verbosity=2).run(suite)
