#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Test module for starting the broker."""

import os
import sys
import unittest
from tempfile import mkdtemp
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

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
        twistd = os.path.join(config.get("broker", "srcdir"),
                              "lib", "python2.6", "aquilon", "unittest_patches.py")
        pidfile = os.path.join(config.get("broker", "rundir"), "aqd.pid")
        logfile = config.get("broker", "logfile")

        # Specify twistd and options...
        args = [sys.executable, twistd,
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
        # running '%s -bn aqd --config %s'%(twistd, config.baseconfig)

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
