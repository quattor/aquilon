#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Module for testing the manage command."""


import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestManageValidateBranch(TestBrokerCommand):

    def test_000_add_managetest1_sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "managetest1"])

    def test_000_add_managetest2_sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "managetest2"])

    def test_100_manage_for_uncommitted_change(self):
        # aquilon63.aqd-unittest.ms.com & aquilon64.aqd-unittest.ms.com are
        # sitting in "%s/utsandbox" we manage it to managetest1 to start clean.
        user = self.config.get("unittest", "user")
        self.noouttest(["manage", "--hostname=aquilon63.aqd-unittest.ms.com",
                        "--sandbox=%s/managetest1" % user, "--force"])
        self.noouttest(["manage", "--hostname=aquilon64.aqd-unittest.ms.com",
                        "--sandbox=%s/managetest1" % user, "--force"])

    def test_101_make_uncommitted_change(self):
        sandboxdir = os.path.join(self.sandboxdir, "managetest1")
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="managetest1")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by test_manage unittest %s \n" % sandboxdir)
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["add", template], cwd=sandboxdir)

    def test_102_fail_uncommitted_change(self):
        user = self.config.get("unittest", "user")
        command = ["manage", "--hostname", "aquilon63.aqd-unittest.ms.com",
                   "--sandbox", "%s/managetest2" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The source sandbox managetest1 contains uncommitted"
                         " files.",
                         command)

    def test_110_commit_uncommitted_change(self):
        sandboxdir = os.path.join(self.sandboxdir, "managetest1")
        self.gitcommand(["commit", "-a", "-m",
                         "added test_manage unittest comment"], cwd=sandboxdir)

    def test_112_fail_missing_committed_change_in_template_king(self):
        user = self.config.get("unittest", "user")
        command = ["manage", "--hostname", "aquilon63.aqd-unittest.ms.com",
                   "--sandbox", "%s/managetest2" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The source sandbox managetest1 latest commit has "
                         "not been published to template-king yet.",
                         command)

    def test_114_publish_committed_change(self):
        sandboxdir = os.path.join(self.sandboxdir, "managetest1")
        self.successtest(["publish", "--branch", "managetest1"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_115_fail_missing_committed_change_in_target(self):
        user = self.config.get("unittest", "user")
        command = ["manage", "--hostname", "aquilon63.aqd-unittest.ms.com",
                   "--sandbox", "%s/managetest2" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The target sandbox managetest2 does not contain the "
                         "latest commit from source sandbox managetest1.",
                         command)

    def test_116_pull_committed_change(self):
        kingdir = self.config.get("broker", "kingdir")
        user = self.config.get("unittest", "user")
        managetest2dir = os.path.join(self.sandboxdir, "managetest2")
        self.gitcommand(["pull", "--no-ff", kingdir, "managetest1"],
                        cwd=managetest2dir)

    def test_120_manage_committed(self):
        user = self.config.get("unittest", "user")
        self.noouttest(["manage", "--hostname=aquilon63.aqd-unittest.ms.com",
                        "--sandbox=%s/managetest2" % user])

    def test_121_verify_manage_committed(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname aquilon63.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: aquilon63.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest2" % user, command)

    def test_130_force_manage_committed(self):
        user = self.config.get("unittest", "user")
        self.noouttest(["manage", "--hostname=aquilon64.aqd-unittest.ms.com",
                        "--sandbox=%s/managetest2" % user, "--force"])

    def test_131_verify_force_manage_committed(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname aquilon64.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: aquilon64.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest2" % user, command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManageValidateBranch)
    unittest.TextTestRunner(verbosity=2).run(suite)
