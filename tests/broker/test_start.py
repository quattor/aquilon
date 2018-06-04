#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Test module for starting the broker."""

import os
from tempfile import mkdtemp
from shutil import rmtree

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from .test_restart import TestBrokerReStart


class TestBrokerStart(TestBrokerReStart):

    def testclonetemplateking(self):
        if self.config.has_option("unittest", "template_base"):
            source = self.config.get("unittest", "template_base")
        else:
            source = None

        if not source:
            source = os.path.join(self.config.get("broker", "srcdir"),
                                  "tests/templates")

        dest = self.config.get("broker", "kingdir")
        rmtree(dest, ignore_errors=True)

        env = {}
        env["PATH"] = os.environ.get("PATH", "")
        env["HOME"] = os.environ.get("HOME", "/home/travis")
        git = self.config.lookup_tool("git")
        if source.startswith("git://"):
            # Easy case - just clone the source repository
            start = None
            if self.config.has_option("unittest", "template_alternate_prod"):
                start = self.config.get("unittest", "template_alternate_prod").strip()
            if not start:
                start = "prod"

            self.run_command([git, "clone", "--bare", "--branch", start,
                              "--single-branch", source, dest], env=env)
            if start != "prod":
                self.run_command([git, "branch", "-m", start, "prod"],
                                 env=env, cwd=dest)
        else:
            # The source is just a directory somewhere. Create a temporary git
            # repository which we can then clone
            tmpdir = mkdtemp()
            self.run_command(["rsync", "-aH", source + "/", tmpdir + "/"],
                             env=env)
            self.run_command([git, "init"], cwd=tmpdir, env=env)
            self.run_command([git, "add", "-A"], cwd=tmpdir, env=env)
            self.run_command([git, "commit", "-m", "Initial commit"],
                             cwd=tmpdir, env=env)

            # Create the prod branch
            self.run_command([git, "checkout", "-b", "prod"], cwd=tmpdir, env=env)

            self.run_command([git, "clone", "--bare", tmpdir, dest], env=env)
            rmtree(tmpdir, ignore_errors=True)

        if self.config.has_option("broker", "trash_branch"):
            trash_branch = self.config.get("broker", "trash_branch")
            self.run_command([git, "branch", trash_branch, "prod"],
                             env=env, cwd=dest)

        # Set the default branch
        self.run_command([git, "symbolic-ref", "HEAD", "refs/heads/prod"],
                         env=env, cwd=dest)

    def testdisabletemplatetests(self):
        kingdir = self.config.get("broker", "kingdir")
        rundir = self.config.get("broker", "rundir")
        git = self.config.lookup_tool("git")
        env = {}
        env["PATH"] = os.environ.get("PATH", "")
        env["HOME"] = os.environ.get("HOME", "/home/travis")

        tempdir = mkdtemp(prefix="fixup", dir=rundir)

        self.run_command([git, "clone", "--shared", kingdir, "template-king",
                          "--branch", "prod"], cwd=tempdir, env=env)

        repodir = os.path.join(tempdir, "template-king")
        if os.path.exists(os.path.join(repodir, "t", "Makefile")):
            self.run_command([git, "rm", "-f", os.path.join("t", "Makefile")],
                             cwd=repodir, env=env)
            self.run_command([git, "commit", "-m", "Removed t/Makefile"],
                             cwd=repodir, env=env)

            for branch in ['prod']:
                self.run_command([git, "push", "origin", "prod:%s" % branch],
                                 cwd=repodir, env=env)

        rmtree(tempdir, ignore_errors=True)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStart)
    unittest.TextTestRunner(verbosity=2).run(suite)
