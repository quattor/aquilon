#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
import sys
from tempfile import mkdtemp
from shutil import rmtree
from subprocess import Popen, PIPE

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from aquilon.config import Config


class TestBrokerStart(unittest.TestCase):

    config = None

    @classmethod
    def setUpClass(cls):
        cls.config = Config()

    def run_command(self, command, **kwargs):
        p = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)
        out, err = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Command '%s' returned %d:"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@\n"
                         "\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (command, p.returncode, out, err))

    def teststart(self):
        # FIXME: Either remove any old pidfiles, or ignore it as a warning
        # from stderr... or IMHO (daqscott) if pid files exist and are knc or
        # python processes, kill -9 the pids and delete the files (with a
        # warning message it tickles you)

        aqd = os.path.join(self.config.get("broker", "srcdir"),
                           "lib", "aquilon", "unittest_patches.py")
        pidfile = os.path.join(self.config.get("broker", "rundir"), "aqd.pid")
        logfile = self.config.get("broker", "logfile")

        # Specify aqd and options...
        args = [sys.executable, aqd,
                "--pidfile", pidfile, "--logfile", logfile]

        if self.config.has_option("unittest", "profile"):
            if self.config.getboolean("unittest", "profile"):
                args.append("--profile")
                args.append(os.path.join(self.config.get("broker", "logdir"),
                                         "aqd.profile"))
                args.append("--profiler=cProfile")
                args.append("--savestats")

        # And then aqd and options...
        args.extend(["aqd", "--config", self.config.baseconfig])

        if self.config.has_option("unittest", "coverage"):
            if self.config.getboolean("unittest", "coverage"):
                args.append("--coveragedir")
                dir = os.path.join(self.config.get("broker", "logdir"), "coverage")
                args.append(dir)

                coveragerc = os.path.join(self.config.get("broker", "srcdir"),
                                          "tests", "coverage.rc")
                args.append("--coveragerc")
                args.append(coveragerc)

        self.run_command(args)

        # FIXME: Check that it is listening on the correct port(s)...

        # FIXME: If it fails, either cat the log file, or tell the user to try
        # running '%s -bn aqd --config %s'%(aqd, self.config.baseconfig)

    def testeventsstart(self):
        # pidfile = os.path.join(self.config.get('broker', 'rundir'), 'read_events.pid')
        read_events = os.path.join(self.config.get('broker', 'srcdir'),
                                   'tests', 'read_events.py')
        args = [sys.executable, read_events, '--store', '--daemon',
                '--config', self.config.baseconfig]
        self.run_command(args)

    def testclonetemplateking(self):
        source = self.config.get("unittest", "template_base")
        if not source:
            source = os.path.join(self.config.get("broker", "srcdir"),
                                  "tests/templates")

        dest = self.config.get("broker", "kingdir")
        rmtree(dest, ignore_errors=True)

        env = {}
        env["PATH"] = os.environ.get("PATH", "")
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

    def testsetuppanclinks(self):
        # Some tests want multiple versions of panc.jar available. Nothing
        # depends on the behavior being different, so a couple symlinks will do
        # the job
        real_panc = self.config.get("unittest", "real_panc_location")
        fake_panc_default = self.config.get("panc", "pan_compiler")
        fake_panc_utpanc = self.config.get("panc", "pan_compiler",
                                           vars={'version': 'utpanc'})

        fake_panc_dir = os.path.dirname(fake_panc_default)
        if not os.path.exists(fake_panc_dir):
            os.makedirs(fake_panc_dir, 0o755)

        for dst in (fake_panc_default, fake_panc_utpanc):
            try:
                os.unlink(dst)
            except OSError:
                pass
            os.symlink(real_panc, dst)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStart)
    unittest.TextTestRunner(verbosity=2).run(suite)
