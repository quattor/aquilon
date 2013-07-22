#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from aquilon.config import Config


class TestBrokerStart(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def teststart(self):
        # FIXME: Either remove any old pidfiles, or ignore it as a warning
        # from stderr... or IMHO (daqscott) if pid files exist and are knc or
        # python processes, kill -9 the pids and delete the files (with a
        # warning message it tickles you)

        config = Config()
        aqd = os.path.join(config.get("broker", "srcdir"),
                           "lib", "aquilon", "unittest_patches.py")
        pidfile = os.path.join(config.get("broker", "rundir"), "aqd.pid")
        logfile = config.get("broker", "logfile")

        # Specify aqd and options...
        args = [sys.executable, aqd,
                "--pidfile", pidfile, "--logfile", logfile]

        if config.has_option("unittest", "profile"):
            if config.getboolean("unittest", "profile"):
                args.append("--profile")
                args.append(os.path.join(config.get("broker", "logdir"),
                                         "aqd.profile"))
                args.append("--profiler=cProfile")
                args.append("--savestats")

        # And then aqd and options...
        args.extend(["aqd", "--config", config.baseconfig])

        if config.has_option("unittest", "coverage"):
            if config.getboolean("unittest", "coverage"):
                args.append("--coveragedir")
                dir = os.path.join(config.get("broker", "logdir"), "coverage")
                args.append(dir)

                coveragerc = os.path.join(config.get("broker", "srcdir"),
                                          "tests", "coverage.rc")
                args.append("--coveragerc")
                args.append(coveragerc)

        p = Popen(args)
        self.assertEqual(p.wait(), 0)

        # FIXME: Check that it is listening on the correct port(s)...

        # FIXME: If it fails, either cat the log file, or tell the user to try
        # running '%s -bn aqd --config %s'%(aqd, config.baseconfig)

    def testclonetemplateking(self):
        config = Config()
        source = config.get("unittest", "template_base")
        dest = config.get("broker", "kingdir")
        p = Popen(("/bin/rm", "-rf", dest), stdout=1, stderr=2)
        rc = p.wait()
        self.assertEqual(rc, 0,
                         "Failed to clear old template-king directory '%s'" %
                         dest)
        env = {}
        env["PATH"] = "%s:%s" % (config.get("broker", "git_path"),
                                 os.environ.get("PATH", ""))
        p = Popen(("git", "clone", "--bare", source, dest),
                  env=env, stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for clone of template-king, "
                         "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (out, err))
        # This value can be used to test against a different branch/commit
        # than the current 'prod'.
        new_prod = None
        if config.has_option("unittest", "template_alternate_prod"):
            new_prod = config.get("unittest", "template_alternate_prod")

        if new_prod:
            for domain in ['prod', 'ny-prod']:
                p = Popen(("git", "push", ".", '+%s:%s' % (new_prod, domain)),
                          env=env, cwd=dest, stdout=PIPE, stderr=PIPE)
                (out, err) = p.communicate()
                # Ignore out/err unless we get a non-zero return code, then log it.
                self.assertEqual(p.returncode, 0,
                                 "Non-zero return code while setting alternate "
                                 "'%s' branch locally to '%s':"
                                 "\nSTDOUT:\n@@@\n'%s'\n@@@\n"
                                 "\nSTDERR:\n@@@\n'%s'\n@@@\n"
                                 % (domain, new_prod, out, err))

        # Set the default branch
        p = Popen(("git", "symbolic-ref", "HEAD", "refs/heads/prod"),
                  env=env, cwd=dest, stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code while setting HEAD "
                         "to refs/heads/prod:"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@\n"
                         "\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (out, err))
        return

    def testcloneswrep(self):
        config = Config()
        source = config.get("unittest", "swrep_repository")
        dest = os.path.join(config.get("broker", "swrepdir"), "repository")
        p = Popen(("/bin/rm", "-rf", dest), stdout=1, stderr=2)
        rc = p.wait()
        self.assertEqual(rc, 0,
                         "Failed to clear old swrep directory '%s'" %
                         dest)
        env = {}
        env["PATH"] = "%s:%s" % (config.get("broker", "git_path"),
                                 os.environ.get("PATH", ""))
        p = Popen(("git", "clone", source, dest),
                  env=env, stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for clone of swrep, "
                         "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (out, err))
        return

    def testdisabletemplatetests(self):
        config = Config()
        kingdir = config.get("broker", "kingdir")
        rundir = config.get("broker", "rundir")
        env = {}
        env["PATH"] = "%s:%s" % (config.get("broker", "git_path"),
                                 os.environ.get("PATH", ""))

        tempdir = mkdtemp(prefix="fixup", dir=rundir)

        p = Popen(("git", "clone", "--shared", kingdir, "template-king",
                   "--branch", "prod"),
                  cwd=tempdir, env=env, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        self.assertEqual(p.returncode, 0, "Failed to clone template-king")

        repodir = os.path.join(tempdir, "template-king")
        makefile = os.path.join(repodir, "Makefile")
        if os.path.exists(os.path.join(repodir, "t", "Makefile")):
            p = Popen(("git", "rm", "-f", os.path.join("t", "Makefile")),
                      cwd=repodir, env=env, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            self.assertEqual(p.returncode, 0, "Failed to remove t/Makefile")

            p = Popen(("git", "commit", "-m", "Removed t/Makefile"),
                      cwd=repodir, env=env, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            self.assertEqual(p.returncode, 0, "Failed to commit removal of t/Makefile")

            for branch in ['prod', 'ny-prod']:
                p = Popen(("git", "push", "origin", "prod:%s" % branch),
                          cwd=repodir, env=env, stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                self.assertEqual(p.returncode, 0,
                                 "Failed to push to %s, "
                                 "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                                 % (branch, out, err))
        p = Popen(("rm", "-rf", tempdir))
        p.communicate()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStart)
    unittest.TextTestRunner(verbosity=2).run(suite)
