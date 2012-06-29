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
    import broker.utils
    broker.utils.import_depends()

from broker.brokertest import TestBrokerCommand

ARCHETYPE = 'aquilon'

FEATURE = 'myfeature'

PARAM_DEFS = [	{ "path" : "netgroup",
                  "value_type" : "list",
                  "description" : "netgroups access",
                  "template" : "access"
                },

		{ "path" : "users",
                  "value_type" : "list",
                  "description" : "users access",
                  "template" : "access",
		},

		{ "path" : "lastacl",
                  "value_type" : "list",
                  "description" : "acl access",
                  "template" : "access",
		},

		{ "path" : "action/\w+/user",
                  "value_type" : "string",
                  "description" : "action user",
                  "template" : "actions",
                },

		{ "path" : "action/\w+/command",
                  "value_type" : "string",
                  "description" : "action command",
                  "template" : "actions",
                },

		{ "path" : "function",
                  "value_type" : "string",
                  "description" : "espinfo function",
                  "template" : "espinfo",
		  "required" : True,
		},

		{ "path" : "security_class",
                  "value_type" : "string",
                  "description" : "security class",
                  "template" : "security",
		  "required" : True,
		  "default" : "internal-isg-relaxed",
		  "required" : True,
		},

		{ "path" : "filesystem_layout",
                  "value_type" : "string",
                  "description" : "filesystem layout",
                  "template" : "security",
		  "required" : True,
		  "default" : "afs",
		}
]

class TestParameterDefinition(TestBrokerCommand):

    def test_100_add(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--template=foo", "--required", "--default=default"]

        self.noouttest(cmd)

    def test_110_add_existing(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--template=foo", "--required", "--default=default"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "ParamDefinition path testpath, archetypeparamdef archetype already exists", cmd)

    def test_130_add_default_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testdefault", "--description=blaah",
               "--template=foo" ]

        err = self.noouttest(cmd)

    def test_130_add_int_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testint", "--description=blaah",
               "--template=foo", "--value_type=int", "--default=60"]

        err = self.noouttest(cmd)

    def test_130_add_invalid_int_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadint", "--description=blaah",
               "--template=foo", "--value_type=int", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an integer for default for path=testbadint", cmd)

    def test_130_add_float_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testfloat", "--description=blaah",
               "--template=foo", "--value_type=float", "--default=100.100"]

        err = self.noouttest(cmd)

    def test_130_add_invalid_float_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadfloat", "--description=blaah",
               "--template=foo", "--value_type=float", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an floating point number for default for path=testbadfloat", cmd)

    def test_130_add_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testboolean", "--description=blaah",
               "--template=foo", "--value_type=boolean", "--default=yes"]

        err = self.noouttest(cmd)

    def test_130_add_invalid_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadboolean", "--description=blaah",
               "--template=foo", "--value_type=boolean", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected a boolean value for default for path=testbadboolean", cmd)

    def test_130_add_list_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testlist", "--description=blaah",
               "--template=foo", "--value_type=list", "--default=val1,val2"]

        err = self.noouttest(cmd)

    def test_130_add_json_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testjson", "--description=blaah",
               "--template=foo", "--value_type=json","--default=\"{'val1':'val2'}\""]

        err = self.noouttest(cmd)

    def test_130_add_invalid_json_value_type(self):
        cmd = ["add_parameter_definition", "--archetype", ARCHETYPE,
               "--path=testbadjson", "--description=blaah",
               "--template=foo", "--value_type=json","--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "The json string specified for default for path=testbadjson is invalid", cmd)

    def test_140_verify_add(self):
        cmd = ["show", "parameter_definition", "--archetype", ARCHETYPE ]

        out = self.commandtest(cmd)
        self.matchoutput(out, "Required:\n  parameter: testpath  value type:string  template:foo  default:default", cmd)
        self.matchoutput(out, "parameter: testdefault  value type:string  template:foo", cmd)
        self.matchoutput(out, "parameter: testint  value type:int  template:foo  default:60", cmd)
        self.matchoutput(out, "parameter: testjson  value type:json  template:foo  default:\"{'val1':'val2'}\"", cmd)
        self.matchoutput(out, "parameter: testlist  value type:list  template:foo  default:val1,val2 ", cmd)

    def test_150_del(self):

        for path in ['testpath','testdefault','testint', 'testlist', 'testjson', 'testboolean', 'testfloat']:
            cmd = ["del_parameter_definition", "--archetype", ARCHETYPE,
                   "--path=%s" % path ]
            self.noouttest(cmd)

    def test_150_verify_delete(self):
        cmd = ["show", "parameter_definition", "--archetype", ARCHETYPE ]

        err = self.notfoundtest(cmd)
        self.matchoutput(err, "Not Found: No parameter definitions found for archetype aquilon", cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterDefintion)
    unittest.TextTestRunner(verbosity=2).run(suite)

