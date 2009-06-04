#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008  Contributor
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
"""Module for testing the add domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddDomain(TestBrokerCommand):

    def testaddunittestdomain(self):
        self.noouttest(["add", "domain", "--domain", "unittest"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "unittest")))

    def testverifyaddunittestdomain(self):
        command = "show domain --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: unittest", command)

    def testaddchangetest1domain(self):
        self.noouttest(["add", "domain", "--domain", "changetest1"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest1")))

    def testverifyaddchangetest1domain(self):
        command = "show domain --domain changetest1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetest1", command)

    def testaddchangetest2domain(self):
        self.noouttest(["add", "domain", "--domain", "changetest2"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest2")))

    def testverifyaddchangetest2domain(self):
        command = "show domain --domain changetest2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetest2", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

