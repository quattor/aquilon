#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" Used by the test runner to display what test is currently running """
import unittest

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

    def addError(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addError(self, test, err)
        self.printResult("ERROR", self.errors[-1])

    def addFailure(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addFailure(self, test, err)
        self.printResult("FAIL", self.failures[-1])


class VerboseTextTestRunner(unittest.TextTestRunner):

    def _makeResult(self):
        return VerboseTextTestResult(self.stream, self.descriptions,
                                     self.verbosity)
