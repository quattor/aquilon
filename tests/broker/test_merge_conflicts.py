#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing that we handle merge conflicts properly"""

import os
from shutil import rmtree

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestMergeConflicts(TestBrokerCommand):

    def test_100_addchangetest3sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "changetest3"])

    def test_100_addchangetest4sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "changetest4"])

    def test_100_addchangetargetdomain(self):
        self.successtest(["add", "domain", "--domain", "changetarget", "--justification", "tcm=123"])

    def test_110_trackchangetest4(self):
        self.commandtest(["add_domain", "--domain", "changetest4-tracker",
                          "--track", "changetest4", "--justification", "tcm=123"])

    def test_110_trackchangetarget(self):
        self.commandtest(["add_domain", "--domain", "changetarget-tracker",
                          "--track", "changetarget", "--justification", "tcm=123"])

    def test_120_makeconflictingchange(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="changetest3")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by changetest3\n")

        with open(template, 'w') as f:
            f.writelines(contents)

        self.gitcommand(["commit", "-a", "-m", "added changetest3 comment"],
                        cwd=sandboxdir)

        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="changetest4")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by changetest4\n")

        with open(template, 'w') as f:
            f.writelines(contents)

        self.gitcommand(["commit", "-a", "-m", "added changetest4 comment"],
                        cwd=sandboxdir)

    def test_121_publishchangetest3sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        self.successtest(["publish", "--branch", "changetest3"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_121_publishchangetest4sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.successtest(["publish", "--branch", "changetest4"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_122_deploychangetest3sandbox(self):
        command = ["deploy", "--source", "changetest3", "--target", "changetarget"]
        out = self.statustest(command)
        self.matchoutput(out, "Updating the checked out copy of domain "
                         "changetarget...", command)
        self.matchoutput(out, "Updating the checked out copy of domain "
                         "changetarget-tracker...", command)
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="changetarget")
        with open(template) as f:
            contents = f.readlines()

        self.assertEqual(contents[-1], "#Added by changetest3\n")

    def test_122_deploychangetest4sandbox(self):
        command = "deploy --source changetest4 --target changetarget"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Automatic merge failed;", command)

        repo = os.path.join(self.config.get("broker", "domainsdir"),
                            "changetarget")
        self.check_git_merge_health(repo)

    def test_123_prepchangetest4sandbox(self):
        # Fix up the branch and get it ready for a successful put.
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.gitcommand(["fetch"], cwd=sandboxdir)
        command = ["merge", "origin/changetest3"]
        out, _ = self.gitcommand_expectfailure(command, cwd=sandboxdir)
        self.matchoutput(out, "Automatic merge failed;", command)

        # The file will now have merge conflicts.  Cheat by grabbing
        # the copy from changetest3.
        for ext in [".tpl", ".pan"]:
            base = os.path.join("aquilon", "archetype", "base" + ext)
            if os.path.exists(os.path.join(sandboxdir, base)):
                break
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

    def test_124_prepchangetest3conflict(self):
        # Model someone doing a put of a conflicting change by forgetting
        # that *we* put the conflicting change. :)  Having two users doing
        # two different put operations on a sandbox is hard in this
        # framework.  Instead, we fake it by rewinding the sandbox to the
        # previous commit!
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        self.gitcommand(["reset", "--hard", "HEAD^1"], cwd=sandboxdir)
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="changetest3")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by prepchangetest3conflict\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        self.gitcommand(["commit", "-a", "-m",
                         "added prepchangetest3conflict comment"],
                        cwd=sandboxdir)

    def test_125_publishchangetest3sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        command = ["publish", "--branch=changetest3"]
        # Ignore STDOUT messages explaining what will be pushed.
        out = self.badrequesttest(command, ignoreout=True,
                                  env=self.gitenv(), cwd=sandboxdir)
        self.matchoutput(out, "rejected", command)
        self.matchoutput(out, "non-fast-forward", command)
        # Should this try to verify template-king's changetest3 branch?
        # Can't check merge health on king because it's a bare repo.
        # kingdir = self.config.get("broker", "kingdir")
        # self.check_git_merge_health(kingdir)

    def test_126_publishchangetest4sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.successtest(["publish", "--branch", "changetest4"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_127_deploychangetest4sandbox(self):
        command = "deploy --source changetest4 --target changetarget"
        self.successtest(command.split(" "))

        repo = os.path.join(self.config.get("broker", "domainsdir"),
                            "changetarget")
        self.check_git_merge_health(repo)

        template = self.find_template("aquilon", "archetype", "base",
                                      domain="changetarget-tracker")
        with open(template) as f:
            contents = f.readlines()
        self.assertEqual(contents[-1], "#Added by changetest4\n")

    def test_130_add_changetest5_sandbox(self):
        self.successtest(["add", "sandbox", "--sandbox", "changetest5"])

    def test_131_prepare_changetest5(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest5")
        filename = os.path.join(sandboxdir, "changetest5.txt")

        with open(filename, "w") as f:
            f.write("Added by changetest5\n")

        self.gitcommand(["add", "changetest5.txt"], cwd=sandboxdir)
        self.gitcommand(["commit", "-a", "-m", "added changetest5 comment"],
                        cwd=sandboxdir)

    def test_132_publish_changetest5(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest5")
        self.successtest(["publish", "--branch", "changetest5"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_135_rollback_no_history(self):
        command = ["rollback", "--domain", "changetarget-tracker",
                   "--ref", "changetest5", "--justification", "tcm=123"]
        out = self.badrequesttest(command)
        self.searchoutput(out, "Cannot roll back to commit: "
                          "branch changetarget does not contain", command)

    def test_140_rollback(self):
        command = "rollback --domain changetarget-tracker --lastsync --justification tcm=123"
        self.successtest(command.split(" "))
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="changetarget-tracker")
        with open(template) as f:
            contents = f.readlines()
        self.assertNotEqual(contents[-1], "#Added by changetest4\n")

    def test_145_failreverserollback(self):
        command = "sync --domain changetarget-tracker"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Tracked branch changetarget is set to not "
                         "allow sync.  Run aq validate",
                         command)
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="changetarget-tracker")
        with open(template) as f:
            contents = f.readlines()
        self.assertNotEqual(contents[-1], "#Added by changetest4\n")

    def test_150_deploy_after_rollback(self):
        command = ["deploy", "--source", "changetest5",
                   "--target", "changetarget"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Domain changetarget has not been validated",
                         command)

    def test_151_deploy_after_rollback_nosync(self):
        command = ["deploy", "--source", "changetest5",
                   "--target", "changetarget", "--nosync"]
        out = self.statustest(command)
        self.matchoutput(out, "Updating the checked out copy of domain "
                         "changetarget...", command)
        self.matchclean(out, "changetarget-tracker", command)

    def test_152_verify_tracker_directory(self):
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "changetarget-tracker")
        filename = os.path.join(domaindir, "changetest5.txt")
        self.assertFalse(os.path.exists(filename))

    def test_160_validate(self):
        command = "validate --branch changetarget"
        self.commandtest(command.split(" "))

    def test_165_reverserollback(self):
        command = "sync --domain changetarget-tracker"
        out = self.statustest(command.split(" "))
        self.matchoutput(out, "Updating the checked out copy of domain "
                         "changetarget-tracker...", command)
        template = self.find_template("aquilon", "archetype", "base",
                                      domain="changetarget-tracker")
        with open(template) as f:
            contents = f.readlines()
        self.assertEqual(contents[-1], "#Added by changetest4\n")

        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "changetarget-tracker")
        filename = os.path.join(domaindir, "changetest5.txt")
        self.assertTrue(os.path.exists(filename))

    def test_200_rollback_bad_commit(self):
        # This commit ID is from the Linux kernel sources
        command = ["rollback", "--domain", "changetarget-tracker",
                   "--ref", "2dcd0af568b0cf583645c8a317dd12e344b1c72a", "--justification", "tcm=123"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Ref 2dcd0af568b0cf583645c8a317dd12e344b1c72a "
                         "could not be translated to an existing commit ID.",
                         command)

    def test_200_faildeltrackedsandbox(self):
        command = "del sandbox --sandbox changetest4"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Sandbox changetest4 is tracked by "
                         "['changetest4-tracker']",
                         command)

    def test_800_delchangetest4tracker(self):
        command = "del domain --domain changetest4-tracker"
        self.noouttest(command.split(" "))

    def test_805_verifydelchangetest4tracker(self):
        command = "show domain --domain changetest4-tracker"
        self.notfoundtest(command.split(" "))

    def test_810_delchangetargettracker(self):
        command = "del domain --domain changetarget-tracker"
        self.noouttest(command.split(" "))

    def test_815_verifydelchangetargettracker(self):
        command = "show domain --domain changetarget-tracker"
        self.notfoundtest(command.split(" "))

    # FIXME: should del_sandbox a sandbox with undeployed changes.
    def test_820_delchangetest3sandbox(self):
        command = "del sandbox --sandbox changetest3"
        self.statustest(command.split(" "))
        # This just deletes the branch, so the directory should still be there.
        sandboxdir = os.path.join(self.sandboxdir, "changetest3")
        self.assertTrue(os.path.exists(sandboxdir))
        rmtree(sandboxdir)

    def test_825_verifydelchangetest3sandbox(self):
        command = "show sandbox --sandbox changetest3"
        self.notfoundtest(command.split(" "))

    def test_830_delchangetest4sandbox(self):
        command = "del sandbox --sandbox changetest4"
        self.statustest(command.split(" "))
        # This just deletes the branch, so the directory should still be there.
        sandboxdir = os.path.join(self.sandboxdir, "changetest4")
        self.assertTrue(os.path.exists(sandboxdir))
        rmtree(sandboxdir)

    def test_840_archive_changetarget(self):
        self.noouttest(["update_domain", "--domain=changetarget", "--archived"])

    def test_845_del_changetarget(self):
        command = "del domain --domain changetarget --justification=tcm=12345678"
        self.noouttest(command.split(" "))
        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "changetest")))

    def test_850_del_changetest5(self):
        self.statustest(["del_sandbox", "--sandbox", "changetest5"])
        sandboxdir = os.path.join(self.sandboxdir, "changetest5")
        self.assertTrue(os.path.exists(sandboxdir))
        rmtree(sandboxdir)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMergeConflicts)
    unittest.TextTestRunner(verbosity=2).run(suite)
