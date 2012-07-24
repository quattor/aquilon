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

FEATURE = 'myfeature'

class TestParameterDefinitionFeature(TestBrokerCommand):

    def test_00_add_feature(self):
        cmd = ["add_feature", "--feature", FEATURE, "--type=host" ]
        self.noouttest(cmd)

    def test_100_add(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--required", "--default=default"]

        self.noouttest(cmd)

    def test_110_add_existing(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testpath", "--value_type=string", "--description=blaah",
               "--required", "--default=default"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err,
                         "Parameter Definition testpath, parameter "
                         "definition holder myfeature already exists.",
                         cmd)

    def test_130_add_default_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testdefault", "--description=blaah" ]

        err = self.noouttest(cmd)

    def test_130_add_int_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testint", "--description=blaah",
               "--value_type=int", "--default=60"]

        err = self.noouttest(cmd)

    def test_130_add_invalid_int_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testbadint", "--description=blaah",
               "--value_type=int", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an integer for default for path=testbadint", cmd)

    def test_130_add_float_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testfloat", "--description=blaah",
               "--value_type=float", "--default=100.100"]

        err = self.noouttest(cmd)

    def test_130_add_invalid_float_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testbadfloat", "--description=blaah",
               "--value_type=float", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected an floating point number for default for path=testbadfloat", cmd)

    def test_130_add_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testboolean", "--description=blaah",
               "--value_type=boolean", "--default=yes"]

        err = self.noouttest(cmd)

    def test_130_add_invalid_boolean_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testbadboolean", "--description=blaah",
               "--value_type=boolean", "--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "Expected a boolean value for default for path=testbadboolean", cmd)

    def test_130_add_list_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testlist", "--description=blaah",
               "--value_type=list", "--default=val1,val2"]

        err = self.noouttest(cmd)

    def test_130_add_json_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testjson", "--description=blaah",
               "--value_type=json","--default=\"{'val1':'val2'}\""]

        err = self.noouttest(cmd)

    def test_130_add_invalid_json_value_type(self):
        cmd = ["add_parameter_definition", "--feature", FEATURE, "--feature_type=host",
               "--path=testbadjson", "--description=blaah",
               "--value_type=json","--default=foo"]

        err = self.badrequesttest(cmd)
        self.matchoutput(err, "The json string specified for default for path=testbadjson is invalid", cmd)

    def test_140_verify_add(self):
        cmd = ["show", "parameter_definition", "--feature", FEATURE,
               "--type", "host"]

        out = self.commandtest(cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testpath \[required\]\s*'
                          r'Type: string\s*'
                          r'Default: default',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testdefault\s*'
                          r'Type: string',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testint\s*'
                          r'Type: int\s*'
                          r'Default: 60',
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testjson\s*'
                          r'Type: json\s*'
                          r"Default: \"{'val1':'val2'}\"",
                          cmd)
        self.searchoutput(out,
                          r'Parameter Definition: testlist\s*'
                          r'Type: list\s*'
                          r'Default: val1,val2',
                          cmd)

    def test_150_del(self):
        for path in ['testpath', 'testdefault', 'testint', 'testlist',
                     'testjson', 'testboolean', 'testfloat']:
            cmd = ["del_parameter_definition", "--feature", FEATURE,
                   "--feature_type=host", "--path=%s" % path ]
            self.noouttest(cmd)

    def test_150_verify_delete(self):
        cmd = ["show", "parameter_definition", "--feature", FEATURE,
               "--type", "host"]

        err = self.notfoundtest(cmd)
        self.matchoutput(err, "No parameter definitions found for host "
                         "feature myfeature", cmd)

    def test_999_del(self):
        cmd = ["del_feature", "--feature", FEATURE, "--type=host" ]
        self.noouttest(cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterDefintionFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)

