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
"""Module for testing the del sandbox command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
