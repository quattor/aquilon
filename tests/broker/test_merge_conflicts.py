#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2013  Contributor
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
"""Module for testing that we handle merge conflicts properly"""


import os
import unittest
from subprocess import Popen

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestMergeConflicts(TestBrokerCommand):

    def test_000_addchangetest3sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "changetest3"])

    def test_000_verifyaddchangetest3sandbox(self):
        command = "show sandbox --sandbox changetest3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: changetest3", command)

    def test_000_addchangetest4sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "changetest4"])

    def test_000_verifyaddchangetest4sandbox(self):
        command = "show sandbox --sandbox changetest4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: changetest4", command)

    def test_000_addchangetargetdomain(self):
        self.successtest(["add", "domain", "--domain", "changetarget"])

    def test_000_verifyaddchangetargetdomain(self):
        command = "show domain --domain changetarget"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetarget", command)

    def test_001_clearchangetest3sandbox(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.sandboxdir, "changetest3")),
                  stdout=1, stderr=2)
        rc = p.wait()

    def test_001_clearchangetest4sandbox(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.sandboxdir, "changetest4")),
                  stdout=1, stderr=2)
        rc = p.wait()

    def test_001_getchangetest3sandbox(self):
        self.successtest(["get", "--sandbox", "changetest3"])
        self.assert_(os.path.exists(os.path.join(self.sandboxdir,
                                                 "changetest3")))

    def test_001_getchangetest4sandbox(self):
        self.successtest(["get", "--sandbox", "changetest4"])
        self.assert_(os.path.exists(os.path.join(self.sandboxdir,
                                                 "changetest4")))

    def test_001_trackchangetest4(self):
        self.commandtest(["add_domain", "--domain", "changetest4-tracker",
                          "--track", "changetest4"])

    def test_001_trackchangetarget(self):
        self.commandtest(["add_domain", "--domain", "changetarget-tracker",
                          "--track", "changetarget"])

    def test_002_tracktracker(self):
        command = ["add_domain", "--domain=doubletracker",
                   "--track=changetarget-tracker"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot nest tracking.  Try tracking "
                         "domain changetarget directly.",
                         command)

    def test_002_makeconflictingchange(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        template = os.path.join(sandboxdir, "aquilon", "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by changetest3\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m", "added changetest3 comment"],
                        cwd=sandboxdir)

        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        template = os.path.join(sandboxdir, "aquilon", "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by changetest4\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m", "added changetest4 comment"],
                        cwd=sandboxdir)

    def test_003_publishchangetest3sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        self.successtest(["publish", "--branch", "changetest3"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_003_publishchangetest4sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.successtest(["publish", "--branch", "changetest4"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_004_deploychangetest3sandbox(self):
        self.successtest(["deploy", "--source", "changetest3",
                          "--target", "changetarget"])
        template = os.path.join(self.config.get("broker", "domainsdir"),
                                "changetarget",
                                "aquilon", "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        self.assertEqual(contents[-1], "#Added by changetest3\n")

    def test_005_deploychangetest4sandbox(self):
        command = "deploy --source changetest4 --target changetarget"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Automatic merge failed;", command)

        repo = os.path.join(self.config.get("broker", "domainsdir"),
                            "changetarget")
        self.check_git_merge_health(repo)

#   def test_006_prepchangetest4sandbox(self):
#       self.gitcommand(["checkout", "master"],
#               cwd=os.path.join(self.scratchdir, "changetest4"))

#   def test_007_syncchangetest4domain(self):
#       command = "sync --domain changetest4"
#       out = self.badrequesttest(command.split(" "),
#               cwd=os.path.join(self.scratchdir, "changetest4"))
#       self.matchoutput(out, "WARNING: Your domain repository on the broker has been forcefully reset", command)

#   def test_008_syncchangetest4domain(self):
#       command = "sync --domain changetest4"
#       self.ignoreoutputtest(command.split(" "),
#               cwd=os.path.join(self.scratchdir, "changetest4"))

    # FIXME: Renumber and re-order for clarity.
    def test_008_prepchangetest4sandbox(self):
        # Fix up the branch and get it ready for a successful put.
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.gitcommand(["fetch"], cwd=sandboxdir)
        command = ["merge", "origin/changetest3"]
        (out, err) = self.gitcommand_expectfailure(command, cwd=sandboxdir)
        self.matchoutput(out, "Automatic merge failed;", command)

        # The file will now have merge conflicts.  Cheat by grabbing
        # the copy from changetest3.
        base = os.path.join("aquilon", "archetype", "base.tpl")
        self.gitcommand(["checkout", "origin/changetest3", base],
                        cwd=sandboxdir)

        template = os.path.join(sandboxdir, base)
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by changetest4\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        self.gitcommand(["add", base], cwd=sandboxdir)
        self.gitcommand(["commit", "-a", "-m", "added changetest4 comment"],
                        cwd=sandboxdir)

    def test_009_prepchangetest3conflict(self):
        # Model someone doing a put of a conflicting change by forgetting
        # that *we* put the conflicting change. :)  Having two users doing
        # two different put operations on a sandbox is hard in this
        # framework.  Instead, we fake it by rewinding the sandbox to the
        # previous commit!
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        self.gitcommand(["reset", "--hard", "HEAD^1"], cwd=sandboxdir)
        template = os.path.join(sandboxdir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by prepchangetest3conflict\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        self.gitcommand(["commit", "-a", "-m",
                         "added prepchangetest3conflict comment"],
                        cwd=sandboxdir)

    def test_010_publishchangetest3sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        command = ["publish", "--branch=changetest3"]
        # Ignore STDOUT messages explaining what will be pushed.
        out = self.badrequesttest(command, ignoreout=True,
                                  env=self.gitenv(), cwd=sandboxdir)
        self.matchoutput(out, "rejected", command)
        self.matchoutput(out, "non-fast-forward", command)
        # Should this try to verify template-king's changetest3 branch?
        # Can't check merge health on king because it's a bare repo.
        #kingdir = self.config.get("broker", "kingdir")
        #self.check_git_merge_health(kingdir)

    def test_010_publishchangetest4sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.successtest(["publish", "--branch", "changetest4"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_011_deploychangetest4sandbox(self):
        command = "deploy --source changetest4 --target changetarget"
        self.successtest(command.split(" "))

        repo = os.path.join(self.config.get("broker", "domainsdir"),
                            "changetarget")
        self.check_git_merge_health(repo)

        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "changetarget-tracker")
        template = os.path.join(domaindir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by changetest4\n")

    def test_012_rollback(self):
        command = "rollback --domain changetarget-tracker --lastsync"
        self.successtest(command.split(" "))
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "changetarget-tracker")
        template = os.path.join(domaindir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failIfEqual(contents[-1], "#Added by changetest4\n")

    def test_013_failreverserollback(self):
        command = "sync --domain changetarget-tracker"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Tracked branch changetarget is set to not "
                         "allow sync.  Run aq validate",
                         command)
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "changetarget-tracker")
        template = os.path.join(domaindir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failIfEqual(contents[-1], "#Added by changetest4\n")

    def test_014_validate(self):
        command = "validate --branch changetarget"
        self.commandtest(command.split(" "))

    def test_015_reverserollback(self):
        command = "sync --domain changetarget-tracker"
        out = self.commandtest(command.split(" "))
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "changetarget-tracker")
        template = os.path.join(domaindir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by changetest4\n")

#   FIXME: Should test a true merge here...
#   def test_012_mergechangetest3(self):
#       command = ["merge", "--sandbox=changetest3", "--domain=ut-qa"]
#       self.successtest(command)

#       qadir = os.path.join(self.config.get("broker", "domainsdir"), "ut-qa")
#       template = os.path.join(qadir, "aquilon", "archetype", "base.tpl")
#       with open(template) as f:
#           contents = f.readlines()
#       self.failUnlessEqual(contents[-1], "#Added by changetest3\n")

#   def test_013_mergechangetest4(self):
#       command = ["merge", "--sandbox=changetest4", "--domain=ut-qa"]
#       self.successtest(command)

#       qadir = os.path.join(self.config.get("broker", "domainsdir"), "ut-qa")
#       template = os.path.join(qadir, "aquilon", "archetype", "base.tpl")
#       with open(template) as f:
#           contents = f.readlines()
#       self.failUnlessEqual(contents[-2], "#Added by changetest3\n")
#       self.failUnlessEqual(contents[-1], "#Added by changetest4\n")

    def test_017_faildeltrackedsandbox(self):
        command = "del sandbox --sandbox changetest4"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Sandbox changetest4 is tracked by "
                         "['changetest4-tracker']",
                         command)

    def test_018_delchangetest4tracker(self):
        command = "del domain --domain changetest4-tracker"
        self.commandtest(command.split(" "))

    def test_018_delchangetargettracker(self):
        command = "del domain --domain changetarget-tracker"
        self.commandtest(command.split(" "))

    def test_019_verifydelchangetest4tracker(self):
        command = "show domain --domain changetest4-tracker"
        self.notfoundtest(command.split(" "))

    def test_019_verifydelchangetargettracker(self):
        command = "show domain --domain changetarget-tracker"
        self.notfoundtest(command.split(" "))

    # FIXME: should del_sandbox a sandbox with undeployed changes.
    def test_020_delchangetest3sandbox(self):
        command = "del sandbox --sandbox changetest3"
        self.successtest(command.split(" "))
        # This just deletes the branch, so the directory should still be there.
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        self.assert_(os.path.exists(sandboxdir))

    def test_021_verifydelchangetest3sandbox(self):
        command = "show sandbox --sandbox changetest3"
        self.notfoundtest(command.split(" "))

    def test_022_delchangetest4sandbox(self):
        command = "del sandbox --sandbox changetest4"
        self.successtest(command.split(" "))
        # This just deletes the branch, so the directory should still be there.
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.assert_(os.path.exists(sandboxdir))

    def test_023_verifydelchangetest4sandbox(self):
        command = "show sandbox --sandbox changetest4"
        self.notfoundtest(command.split(" "))

    def test_024_delchangetarget(self):
        command = "del domain --domain changetarget"
        self.successtest(command.split(" "))
        self.failIf(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "changetest")))

    def test_025_verifydelchangetarget(self):
        command = "show domain --domain changetarget"
        self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMergeConflicts)
    unittest.TextTestRunner(verbosity=2).run(suite)
