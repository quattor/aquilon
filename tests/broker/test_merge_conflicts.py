#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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

from __future__ import with_statement

import os
import sys
import unittest
from subprocess import Popen

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMergeConflicts(TestBrokerCommand):

    def test_000_addchangetest3domain(self):
        self.noouttest(["add", "domain", "--domain", "changetest3"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest3")))

    def test_000_verifyaddchangetest3domain(self):
        command = "show domain --domain changetest3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetest3", command)

    def test_000_addchangetest4domain(self):
        self.noouttest(["add", "domain", "--domain", "changetest4"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest4")))

    def test_000_verifyaddchangetest4domain(self):
        command = "show domain --domain changetest4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: changetest4", command)

    def test_001_clearchangetest3domain(self):
        p = Popen(("/bin/rm", "-rf",
            os.path.join(self.scratchdir, "changetest3")), stdout=1, stderr=2)
        rc = p.wait()

    def test_001_clearchangetest4domain(self):
        p = Popen(("/bin/rm", "-rf",
            os.path.join(self.scratchdir, "changetest4")), stdout=1, stderr=2)
        rc = p.wait()

    def test_001_getchangetest3domain(self):
        self.ignoreoutputtest(["get", "--domain", "changetest3"],
                cwd=self.scratchdir)
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest3")))

    def test_001_getchangetest4domain(self):
        self.ignoreoutputtest(["get", "--domain", "changetest4"],
                cwd=self.scratchdir)
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest4")))

    def test_002_makeconflictingchange(self):
        template = os.path.join(self.scratchdir, "changetest3", "aquilon",
                "archetype", "base.tpl")
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
                cwd=os.path.join(self.scratchdir, "changetest3"))

        template = os.path.join(self.scratchdir, "changetest4", "aquilon",
                "archetype", "base.tpl")
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
                cwd=os.path.join(self.scratchdir, "changetest4"))

    def test_003_putchangetest3domain(self):
        self.ignoreoutputtest(["put", "--domain", "changetest3"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "changetest3"))
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest3")))

    def test_003_putchangetest4domain(self):
        self.ignoreoutputtest(["put", "--domain", "changetest4"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "changetest4"))
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest4")))


    def test_004_deploychangetest3domain(self):
        self.noouttest(["deploy", "--domain", "changetest3"])
        template = os.path.join(self.config.get("broker", "kingdir"),
                "aquilon", "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        self.assertEqual(contents[-1], "#Added by changetest3\n")

    def test_005_deploychangetest4domain(self):
        command = "deploy --domain changetest4"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Automatic merge failed;", command)

        repo = self.config.get("broker", "kingdir")
        self.check_git_merge_health(repo)

    def test_006_prepchangetest4domain(self):
        self.gitcommand(["checkout", "master"],
                cwd=os.path.join(self.scratchdir, "changetest4"))

    def test_007_syncchangetest4domain(self):
        command = "sync --domain changetest4"
        out = self.badrequesttest(command.split(" "),
                cwd=os.path.join(self.scratchdir, "changetest4"))
        self.matchoutput(out, "WARNING: Your domain repository on the broker has been forcefully reset", command)

    def test_008_syncchangetest4domain(self):
        command = "sync --domain changetest4"
        self.ignoreoutputtest(command.split(" "),
                cwd=os.path.join(self.scratchdir, "changetest4"))

    def test_009_prepchangetest3domain(self):
        # Make a change directly on the server that will conflict
        # with an incoming change.
        # This sets up an unsuccessful put.
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                                 "changetest3")
        template = os.path.join(domaindir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by server-side byprepchangetest3domain\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        self.gitcommand(["commit", "-a", "-m",
                         "added prepchangetest3domain comment"],
                        cwd=domaindir)

        domaindir = os.path.join(self.scratchdir, "changetest3")
        template = os.path.join(domaindir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        contents.append("#Added by shadow-side prepchangetest3domain\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        self.gitcommand(["commit", "-a", "-m",
                         "added prepchangetest3domain comment"],
                        cwd=domaindir)

    def test_009_prepchangetest4domain(self):
        # Fix up the domain and get it ready for a successful put.
        command = "merge changetest4"
        err = self.gitcommand_expectfailure(command.split(" "),
                cwd=os.path.join(self.scratchdir, "changetest4"))
        self.matchoutput(err, "Automatic merge failed;", command)

        file = os.path.join("aquilon", "archetype", "base.tpl")
        self.gitcommand(["add", file],
                cwd=os.path.join(self.scratchdir, "changetest4"))
        template = os.path.join(self.scratchdir, "changetest4", "aquilon",
                "archetype", "base.tpl")
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
                cwd=os.path.join(self.scratchdir, "changetest4"))

    def test_010_putchangetest3domain(self):
        shadow = os.path.join(self.scratchdir, "changetest3")
        command = ["put", "--domain=changetest3"]
        # Can't just use self.badrequesttest() because we need to ignore
        # the output on stdout and deal with mixed output on stderr.
        (p, out, err) = self.runcommand(command, env=self.gitenv(), cwd=shadow)
        self.assertEqual(p.returncode, 4,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 4, out, err))
        self.matchoutput(err, "Bad Request", command)
        self.matchoutput(err, "Merge conflict", command)
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                                 "changetest3")
        self.check_git_merge_health(domaindir)

    def test_010_putchangetest4domain(self):
        self.ignoreoutputtest(["put", "--domain", "changetest4"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "changetest4"))
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest4")))

    def test_011_deploychangetest4domain(self):
        command = "deploy --domain changetest4"
        self.ignoreoutputtest(command.split(" "))

        repo = self.config.get("broker", "kingdir")
        self.check_git_merge_health(repo)

    def test_012_delchangetest3domain(self):
        command = "del domain --domain changetest3"
        self.noouttest(command.split(" "))
        self.assert_(not os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest3")))

    def test_012_verifydelchangetest3domain(self):
        command = "show domain --domain changetest3"
        self.notfoundtest(command.split(" "))

    def test_012_delchangetest4domain(self):
        command = "del domain --domain changetest4"
        self.noouttest(command.split(" "))
        self.assert_(not os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "changetest4")))

    def test_012_verifydelchangetest4domain(self):
        command = "show domain --domain changetest4"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMergeConflicts)
    unittest.TextTestRunner(verbosity=2).run(suite)

