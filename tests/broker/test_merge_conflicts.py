#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing that we handle merge conflicts properly"""

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

    def test_009_prepchangetest4domain(self):
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

