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
"""Module for testing the get domain command."""

import os
import sys
import unittest
from subprocess import Popen

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestGet(TestBrokerCommand):

    def testclearchangetest1domain(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.sandboxdir, "changetest1")),
                  stdout=1, stderr=2)
        rc = p.wait()

    def testclearchangetest2domain(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.sandboxdir, "changetest2")),
                  stdout=1, stderr=2)
        rc = p.wait()

    def testgetchangetest1domain(self):
        (out, err) = self.successtest(["get", "--sandbox", "changetest1"])
        self.failUnless(os.path.exists(os.path.join(self.sandboxdir,
                                                    "changetest1")))

    def testgetchangetest2domain(self):
        user = self.config.get("unittest", "user")
        (out, err) = self.successtest(["get",
                                       "--sandbox=%s/changetest2" % user])
        self.failUnless(os.path.exists(os.path.join(self.sandboxdir,
                                                    "changetest2")))

    def testgetutsandbox(self):
        # This one was added with --noget
        (out, err) = self.successtest(["get", "--sandbox", "utsandbox"])
        self.failUnless(os.path.exists(os.path.join(self.sandboxdir,
                                                    "utsandbox")))

    def testgetbaduser(self):
        command = ["get",
                   "--sandbox", "user-does-not-exist/badbranch"]
        out = self.badrequesttest(command)
        user = self.config.get("unittest", "user")
        self.matchoutput(out,
                         "User '%s' cannot add or get a sandbox on "
                         "behalf of 'user-does-not-exist'." % user,
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGet)
    unittest.TextTestRunner(verbosity=2).run(suite)
