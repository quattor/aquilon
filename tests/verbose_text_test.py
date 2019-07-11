#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2013,2016-2019  Contributor
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
""" Used by the test runner to display what test is currently running """

from subprocess import call
import unittest
import os
from aquilon.config import Config
from aqdb.utils import copy_sqldb
from broker.test_stop import TestBrokerStop


class VerboseTextTestResult(unittest._TextTestResult):
    lastmodule = ""

    def __init__(self, config, stream, descriptions,
                 verbosity, *args, **kwargs):
        self.config = config
        self.verbosity = verbosity
        super(VerboseTextTestResult, self).__init__(stream, descriptions,
                                                    verbosity, *args, **kwargs)

    def printModule(self, test):
        if self.dots:
            if test.__class__.__module__ != self.lastmodule:
                self.lastmodule = test.__class__.__module__
                self.stream.writeln("")
                self.stream.write("%s" % self.lastmodule)

    def addSuccess(self, test):
        self.printModule(test)
        unittest._TextTestResult.addSuccess(self, test)

    def printResult(self, flavour, result):
        (test, err) = result
        self.stream.writeln()
        self.stream.writeln(self.separator1)
        self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))
        self.stream.writeln(self.separator2)
        self.stream.writeln("%s" % err)

    def _cleanup_if_exit(self, test):
        # Kill all test processes before running stop()
        if self.failfast:
            suite = unittest.TestSuite()
            tests = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStop)
            suite.addTest(tests)
            unittest.TextTestRunner(verbosity=self.verbosity).run(suite)
            if "TRAIN_TEST_TYPE" in os.environ:
                print(
                    "UnitTests failed: fix and re-start tests from here with "
                    "'train test -t restart' command. Last test failed: {}.{}"
                    .format(test.__class__.__name__, test._testMethodName))
            else:
                # noinspection PyProtectedMember
                print(
                    'UnitTests failed: fix and re-start tests from failed one '
                    'by passing options: --resume --start {}.{}'
                    .format(test.__class__.__name__, test._testMethodName))

    def addError(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addError(self, test, err)
        self.printResult("ERROR", self.errors[-1])
        copy_sqldb(self.config, target='SNAPSHOT', test=test)
        self._cleanup_if_exit(test)

    def addFailure(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addFailure(self, test, err)
        self.printResult("FAIL", self.failures[-1])
        copy_sqldb(self.config, target='SNAPSHOT', test=test)
        self._cleanup_if_exit(test)


class VerboseTextTestRunner(unittest.TextTestRunner):

    def __init__(self, config, *args, **kwargs):
        self.config = config
        super(VerboseTextTestRunner, self).__init__(*args, **kwargs)

    def _makeResult(self):
        return VerboseTextTestResult(self.config, self.stream, self.descriptions,
                                     self.verbosity)
