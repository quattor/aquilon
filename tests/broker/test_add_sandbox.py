#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Module for testing the add sandbox command."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddSandbox(TestBrokerCommand):

    def testaddutsandbox(self):
        self.noouttest(["add", "sandbox", "--sandbox", "utsandbox",
                        "--comments", "Sandbox used for aqd unit tests",
                        "--noget", "--start=prod"])
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.failIf(os.path.exists(sandboxdir),
                    "Did not expect directory '%s' to exist" % sandboxdir)

    def testverifyaddunittestsandbox(self):
        command = "show sandbox --sandbox utsandbox"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: utsandbox", command)
        self.matchoutput(out, "Comments: Sandbox used for aqd unit tests",
                         command)
        self.matchclean(out, "Path", command)

    def testverifyshowpath(self):
        user = self.config.get("broker", "user")
        command = "show sandbox --sandbox %s/utsandbox --pathonly" % user
        out = self.commandtest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.matchoutput(out, sandboxdir, command)

    def testverifynoauthor(self):
        command = "show sandbox --sandbox utsandbox --pathonly"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Must specify sandbox as author/branch "
                         "when using --pathonly",
                         command)

    def testaddchangetest1sandbox(self):
        user = self.config.get("unittest", "user")
        command = ["add", "sandbox", "--sandbox", "%s/changetest1" % user]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "creating %s" % self.sandboxdir, command)
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def testverifyaddchangetest1sandbox(self):
        user = self.config.get("unittest", "user")
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        command = "show sandbox --sandbox %s/changetest1" % user
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: changetest1", command)
        self.matchoutput(out, "Path: %s" % sandboxdir, command)
        self.matchclean(out, "Comments", command)

    def testaddchangetest2sandbox(self):
        command = ["add", "sandbox", "--sandbox", "changetest2"]
        out = self.commandtest(command)
        sandboxdir = os.path.join(self.sandboxdir, "changetest2")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def testverifyaddchangetest2sandbox(self):
        command = "show sandbox --sandbox changetest2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: changetest2", command)

    def testuppercase1(self):
        # For testing mixed-case add.
        command = ["add", "sandbox", "--sandbox", "CamelCaseTest1"]
        out = self.commandtest(command)
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest1")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def testuppercase2(self):
        # For testing deletion of a sandbox added with mixed case.
        command = ["add", "sandbox", "--sandbox", "CamelCaseTest2"]
        out = self.commandtest(command)
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest2")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def testverifylowerbranchname(self):
        command = ['branch', '-r']
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest1")
        (out, err) = self.gitcommand(command, cwd=sandboxdir)
        self.matchoutput(out, "origin/camelcasetest1", command)

    def testverifyshowmixedcase(self):
        command = "show sandbox --sandbox CamelCaseTest1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: camelcasetest1", command)

    def testverifyshowlowercase(self):
        command = "show sandbox --sandbox camelcasetest1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: camelcasetest1", command)

    def testaddbaduser(self):
        command = ["add", "sandbox",
                   "--sandbox", "user-does-not-exist/badbranch"]
        out = self.badrequesttest(command)
        user = self.config.get("unittest", "user")
        self.matchoutput(out,
                         "User '%s' cannot add or get a sandbox on "
                         "behalf of 'user-does-not-exist'." % user,
                         command)

    def testverifyall(self):
        command = "show sandbox --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: utsandbox", command)
        self.matchoutput(out, "Sandbox: changetest1", command)
        self.matchoutput(out, "Sandbox: changetest2", command)

    def testfailinvalid(self):
        command = "add sandbox --sandbox bad:characters!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "sandbox name 'bad:characters!' is not valid",
                         command)

    def testverifysearch(self):
        user = self.config.get("unittest", "user")
        command = ["search", "sandbox", "--owner", user]
        out = self.commandtest(command)
        self.matchoutput(out, "utsandbox", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
