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

    def testdelutsandbox(self):
        command = "del sandbox --sandbox utsandbox"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def testverifydelutsandbox(self):
        command = "show sandbox --sandbox utsandbox"
        self.notfoundtest(command.split(" "))

    def testdelchangetest1sandbox(self):
        command = "del sandbox --sandbox changetest1"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def testverifydelchangetest1sandbox(self):
        command = "show sandbox --sandbox changetest1"
        self.notfoundtest(command.split(" "))

    def testdelchangetest2sandbox(self):
        command = "del sandbox --sandbox changetest2"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        sandboxdir = os.path.join(self.sandboxdir, "changetest2")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def testdelextrachangetest2(self):
        command = "del sandbox --sandbox changetest2"
        (p, out, err) = self.runcommand(command.split(" "))
        self.assertEqual(p.returncode, 4,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 4, out, err))
        sandboxdir = os.path.join(self.sandboxdir, "changetest2")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)
        self.matchoutput(err,
                         "No aqdb record for sandbox changetest2 was found",
                         command)

    def testverifydelchangetest2sandbox(self):
        command = "show sandbox --sandbox changetest2"
        self.notfoundtest(command.split(" "))

    def testdelcamelcasetest1sandbox(self):
        command = "del sandbox --sandbox CamelCaseTest1"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest1")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def testdelcamelcasetest2sandbox(self):
        command = "del sandbox --sandbox camelcasetest2"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest2")
        self.matchoutput(err, "please `rm -rf %s`" % sandboxdir, command)

    def testdelnonexisting(self):
        command = "del sandbox --sandbox sandbox-does-not-exist"
        (p, out, err) = self.runcommand(command.split(" "))
        self.assertEqual(p.returncode, 4,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 4, out, err))
        self.matchclean(err, "please `rm -rf", command)
        self.matchoutput(err,
                         "Not Found: No aqdb record for sandbox "
                         "sandbox-does-not-exist was found",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
