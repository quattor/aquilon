#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the publish command."""

import os
from shutil import copy, rmtree
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestPublishSandbox(TestBrokerCommand):

    @classmethod
    def setUpClass(cls):
        super(TestPublishSandbox, cls).setUpClass()

        # Run "make clean" on templates before anything else.
        testdir = os.path.join(cls.sandboxdir, "changetest1", "t")
        if os.path.exists(os.path.join(testdir, "Makefile")):
            p = Popen(('/usr/bin/make', 'clean'),
                      cwd=testdir, env=cls.gitenv(env={'PATH': '/bin:/usr/bin'}),
                      stdout=PIPE, stderr=PIPE)
            (out, err) = p.communicate()
            self.assertEqual(p.returncode, 0,
                             "Non-zero return code running make clean in sandbox,"
                             " STDOUT:\n@@@'%s'\n@@@\nSTDERR:\n@@@'%s'@@@\n"
                             % (out, err))

    def testmakechange(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="changetest1")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m", "added unittest comment"],
                        cwd=sandboxdir)

    def testpublishchangetest1sandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        self.successtest(["publish", "--branch", "changetest1"],
                         env=self.gitenv(), cwd=sandboxdir)
        # FIXME: Check the branch on the broker directly?

    def testverifychangetest1(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        p = Popen(["/bin/rm", "-rf", sandboxdir], stdout=1, stderr=2)
        rc = p.wait()
        self.successtest(["get", "--sandbox", "changetest1"])
        self.failUnless(os.path.exists(sandboxdir))
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="changetest1")
        self.failUnless(os.path.exists(template),
                        "aq get did not retrive '%s'" % template)
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")

    def testaddutfiles(self):
        src_dir = os.path.join(self.config.get("unittest", "datadir"),
                               "utsandbox")
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        for root, dirs, files in os.walk(src_dir):
            relpath = root[len(src_dir) + 1:]
            dst_dir = os.path.join(sandboxdir, relpath)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file in files:
                copy(os.path.join(root, file), os.path.join(dst_dir, file))
                self.gitcommand(["add", os.path.join(relpath, file)],
                                cwd=sandboxdir)
        self.gitcommand(["commit", "-a", "-m", "Added unittest files"],
                        cwd=sandboxdir)

    def testpublishutsandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.ignoreoutputtest(["publish", "--sandbox", "utsandbox"],
                              env=self.gitenv(), cwd=sandboxdir)
        # FIXME: verify that changes made it to unittest

    def testrebase(self):
        utsandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        (out, err) = self.gitcommand(["rev-list", "--skip=1", "--max-count=1",
                                      "HEAD"], cwd=utsandboxdir)
        self.ignoreoutputtest(["add", "sandbox", "--sandbox", "rebasetest",
                               "--start", "utsandbox"])
        sandboxdir = os.path.join(self.sandboxdir, "rebasetest")

        # Add some new content
        with open(os.path.join(sandboxdir, "TEST"), "w") as f:
            f.writelines(["Added test file"])
        self.gitcommand(["add", "TEST"], cwd=sandboxdir)
        self.gitcommand(["commit", "-m", "Added test file"], cwd=sandboxdir)

        # First publish - no problem, it's a fast-forward
        self.successtest(["publish", "--sandbox", "rebasetest"],
                         env=self.gitenv(), cwd=sandboxdir)

        # Rewrite the last commit
        with open(os.path.join(sandboxdir, "TEST"), "w") as f:
            f.writelines(["Changed test file"])
        self.gitcommand(["add", "TEST"], cwd=sandboxdir)
        self.gitcommand(["commit", "--amend", "--no-edit"], cwd=sandboxdir)

        # Try to publish it
        command = ["publish", "--sandbox", "rebasetest"]
        out = self.badrequesttest(command, env=self.gitenv(), cwd=sandboxdir,
                                  ignoreout=True)
        # This string comes from git, so it may change if git is upgraded
        self.matchoutput(out, "non-fast-forward", command)

        # Publish with rebasing enabled
        command.append("--rebase")
        self.ignoreoutputtest(command, env=self.gitenv(), cwd=sandboxdir)

    def testrebasetoomuch(self):
        utsandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        prod_head, err = self.gitcommand(["rev-parse", "origin/prod"],
                                         cwd=utsandboxdir)
        self.ignoreoutputtest(["add", "sandbox", "--sandbox", "rebasetest2",
                               "--start", "utsandbox"])
        sandboxdir = os.path.join(self.sandboxdir, "rebasetest2")

        # Rewrite history going beyond the starting point of the sandbox
        self.gitcommand(["filter-branch", "--msg-filter", "tr a-z A-Z", "--force",
                         prod_head.strip() + "^..HEAD"], cwd=sandboxdir)

        # Try to publish it
        command = ["publish", "--sandbox", "rebasetest2", "--rebase"]
        out = self.badrequesttest(command, env=self.gitenv(), cwd=sandboxdir,
                                  ignoreout=True)

        self.matchoutput(out, "The published branch no longer contains",
                         command)

    def testzzcleanup(self):
        self.statustest(["del_sandbox", "--sandbox", "rebasetest"])
        sandboxdir = os.path.join(self.sandboxdir, "rebasetest")
        rmtree(sandboxdir, ignore_errors=True)

        self.statustest(["del_sandbox", "--sandbox", "rebasetest2"])
        sandboxdir = os.path.join(self.sandboxdir, "rebasetest2")
        rmtree(sandboxdir, ignore_errors=True)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPublishSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
