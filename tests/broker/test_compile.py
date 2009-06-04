#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Module for testing the compile command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestCompile(TestBrokerCommand):

    def test_000_precompile(self):
        # Before the tests below, make sure everything is up to date.
        command = "compile --domain unittest"
        out = self.commandtest(command.split(" "))

    def test_100_addchange(self):
        # Change the template used by utsi1 clients to trigger a recompile.
        templatedir = os.path.join(self.scratchdir, "unittest")
        template = os.path.join(templatedir, "service", "utsvc", "utsi1",
                                "client", "config.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest broker/test_compile\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m",
                         "modified unit test service instance 1"],
                         cwd=templatedir)
        self.ignoreoutputtest(["put", "--domain", "unittest"],
                              env=self.gitenv(), cwd=templatedir)

    def test_200_compileunittest(self):
        command = "compile --domain unittest"
        out = self.commandtest(command.split(" "))
        # Currently assumes that there is only one client of utsi1.
        # The idea is to check that only that hosts that needed to
        # be compiled actually were.
        self.matchoutput(out, "Updated 1 XML dependencies", command)
        self.matchoutput(out, "Updated 1 makefile dependencies", command)
        self.matchoutput(out, "Updated 1 host XML configs", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompile)
    unittest.TextTestRunner(verbosity=2).run(suite)

