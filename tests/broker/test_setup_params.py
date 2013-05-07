#!/usr/bin/env python2.6
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

## validation parameters by templates
PARAM_DEFS = {
"access": [
    {
        "path": "access/netgroup",
        "value_type": "list",
        "description": "netgroups access"
    },
    {
        "path": "access/users",
        "value_type": "list",
        "description": "users access"
    },
],
"actions": [
    {
        "path": "action/\w+/user",
        "value_type": "string",
        "description": "action user"
    },
    {
        "path": "action/\w+/command",
        "value_type": "string",
        "description": "action command"
    },
    {
        "path": "action/\w+",
        "value_type": "json",
        "description": "per action block"
    },
    {
        "path": "action",
        "value_type": "json",
        "description": "per action block"
    },
],
"startup": [
    {
        "path": "startup/actions",
        "value_type": "list",
        "description": "startup actions"
    },
],
"shutdown": [
    {
        "path": "shutdown/actions",
        "value_type": "list",
        "description": "shutdown actions"
    },
],
"maintenance": [
    {
        "path": "maintenance/actions",
        "value_type": "list",
        "description": "maintenance actions"
    },
],
"monitoring": [
    {
        "path": "monitoring/alert",
        "value_type": "json",
        "description": "monitoring"
    },
],
"espinfo": [
    {
        "path": "espinfo/function",
        "value_type": "string",
        "description": "espinfo function",
        "required": True
    },
    {
        "path": "espinfo/class",
        "value_type": "string",
        "description": "espinfo class",
        "required": True
    },
    {
        "path": "espinfo/users",
        "value_type": "list",
        "description": "espinfo users",
        "required": True
    },
    {
        "path": "espinfo/threshold",
        "value_type": "int",
        "description": "espinfo threshold",
        "required": True
    },
    {
        "path": "espinfo/description",
        "value_type": "string",
        "description": "espinfo desc"
    },
],
"windows": [
    {
        "path": "windows/windows",
        "value_type": "json",
        "required": True,
        "default": '[{"duration": 8, "start": "08:00", "day": "Sun"}]'
    }
],
"testrebuild": [
    {
        "path": "test/rebuild_required",
        "value_type": "string",
        "rebuild_required": True
    }
],

}

class TestSetupParams(TestBrokerCommand):

    def test_000_add_parameter_definitions(self):

        for template in PARAM_DEFS:
            paths = PARAM_DEFS[template]
            for p in paths:
                cmd = ["add_parameter_definition", "--archetype=aquilon",
                       "--path", p["path"], "--template", template,
                       "--value_type", p["value_type"]]
                if "required" in p:
                    cmd.append("--required")
                if "rebuild_required" in p:
                    cmd.append("--rebuild_required")
                if "default" in p:
                    cmd.extend(["--default", p["default"]])

                self.noouttest(cmd)

    def add_parameter(self, archetype, personality, data):
        cmd = ["add_parameter", "--archetype=%s" % archetype,
               "--personality=%s" % personality]
        for key, value in data.items():
            cmd.append("--path=%s" % key)
            cmd.append("--value=%s" % value)
            self.successtest(cmd)

    def test_010_setup_personality(self):
        data = {"espinfo/function" : "development",
                "espinfo/class" : "INFRASTRUCTURE",
                "espinfo/users" : "IT / TECHNOLOGY",
                "espinfo/threshold" : 0 }

        self.add_parameter("aquilon", "compileserver", data)
        self.add_parameter("aquilon", "inventory", data)
        self.add_parameter("aquilon", "eaitools", data)
        self.add_parameter("aquilon", "unixeng-test", data)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSetupParams)
    unittest.TextTestRunner(verbosity=2).run(suite)
