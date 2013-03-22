#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
import unittest
from aquilon.config import Config
from subprocess import call


class VerboseTextTestResult(unittest._TextTestResult):
    lastmodule = ""

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

    def _snapshot_db(self, test):
        # If there was an error, and we're using SQLite, create a snapshot
        # TODO: create a git-managed snapshot of the plenaries/profiles as well
        config = Config()
        dsn = config.get("database", "dsn")
        if dsn.startswith("sqlite:///"):

            dbfile = dsn[10:]
            target = dbfile + ".%s:%s" % (test.__class__.__name__,
                                          test._testMethodName)
            call(["/bin/cp", "-a", dbfile, target])

    def addError(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addError(self, test, err)
        self.printResult("ERROR", self.errors[-1])
        self._snapshot_db(test)

    def addFailure(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addFailure(self, test, err)
        self.printResult("FAIL", self.failures[-1])
        self._snapshot_db(test)


class VerboseTextTestRunner(unittest.TextTestRunner):

    def _makeResult(self):
        return VerboseTextTestResult(self.stream, self.descriptions,
                                     self.verbosity)
