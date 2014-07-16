#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the del sandbox command."""


import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelSandbox(TestBrokerCommand):

    def test_100_del_utsandbox(self):
        command = "del sandbox --sandbox utsandbox"
        err = self.statustest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def test_101_verify_utsandbox(self):
        command = "show sandbox --sandbox utsandbox"
        self.notfoundtest(command.split(" "))

    def test_120_del_changetest1(self):
        command = "del sandbox --sandbox changetest1"
        err = self.statustest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def test_130_del_changetest2(self):
        command = "del sandbox --sandbox changetest2"
        err = self.statustest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "changetest2")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def test_131_del_changetest2_again(self):
        command = "del sandbox --sandbox changetest2"
        err = self.notfoundtest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "changetest2")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)
        self.matchoutput(err, "Sandbox changetest2 not found.", command)

    def test_132_verify_changetest2(self):
        command = "show sandbox --sandbox changetest2"
        self.notfoundtest(command.split(" "))

    def test_140_del_camelcasetest1(self):
        command = "del sandbox --sandbox CamelCaseTest1"
        err = self.statustest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest1")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def test_145_del_camelcasetest2(self):
        command = "del sandbox --sandbox camelcasetest2"
        err = self.statustest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest2")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def test_200_del_nonexisting(self):
        command = "del sandbox --sandbox sandbox-does-not-exist"
        err = self.notfoundtest(command.split(" "))
        self.matchclean(err, "please `rm -rf", command)
        self.matchoutput(err,
                         "Sandbox sandbox-does-not-exist not found.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
