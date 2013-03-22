#!/usr/bin/env python2.6
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
"""Module for testing the publish command."""


import os
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPublishSandbox(TestBrokerCommand):

    def test_001(self):
        """Run "make clean" on templates before anything else.

        Replace with setupClass when we move to Py2.7
        """
        testdir = os.path.join(self.sandboxdir, "changetest1", "t")
        if os.path.exists(os.path.join(testdir, "Makefile")):
            p = Popen(('/usr/bin/make', 'clean'),
                      cwd=testdir, env=self.gitenv(env={'PATH': '/bin:/usr/bin'}),
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

    def testaddsiteut(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        if os.path.exists(os.path.join(sandboxdir, "site")):
            sitedir = os.path.join(sandboxdir, "site")
        else:
            sitedir = os.path.join(sandboxdir, "aquilon", "site")
        utdir = os.path.join(sitedir, "americas", "ny", "ut")
        if not os.path.exists(utdir):
            os.makedirs(utdir)
        template = os.path.join(utdir, "config" + self.template_extension)
        f = open(template, 'w')
        try:
            f.writelines("template site/americas/ny/ut/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config" + self.template_extension], cwd=utdir)
        self.gitcommand(["commit", "-a", "-m", "added building ut"],
                        cwd=sandboxdir)

    def testaddutsi1(self):
        """utsi1 = unit test service instance 1"""
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("service", "utsvc", "utsi1", "client",
                                      "config", sandbox="utsandbox")
        svcdir = os.path.dirname(template)
        if not os.path.exists(svcdir):
            os.makedirs(svcdir)
        f = open(template, 'w')
        try:
            f.writelines("template service/utsvc/utsi1/client/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config" + self.template_extension], cwd=svcdir)
        self.gitcommand(["commit", "-a", "-m",
                         "added unit test service instance 1"],
                        cwd=sandboxdir)

    def testaddutsi2(self):
        """utsi1 = unit test service instance 2"""
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("service", "utsvc", "utsi2", "client",
                                      "config", sandbox="utsandbox")
        svcdir = os.path.dirname(template)
        if not os.path.exists(svcdir):
            os.makedirs(svcdir)
        f = open(template, 'w')
        try:
            f.writelines("template service/utsvc/utsi2/client/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config" + self.template_extension], cwd=svcdir)
        self.gitcommand(["commit", "-a", "-m",
                         "added unit test service instance 2"],
                        cwd=sandboxdir)

    def testaddutpersonality(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("aquilon", "personality",
                                      "utpersonality/dev", "espinfo",
                                      sandbox="utsandbox")
        personalitydir = os.path.dirname(template)
        if not os.path.exists(personalitydir):
            os.makedirs(personalitydir)
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template personality/utpersonality/dev/espinfo;

"name" = "utpersonality/dev";
"description" = "regression test personality";
"class" = "INFRASTRUCTURE";
"infrafunction" = "Sapphire-INV";
"function" = "development";
"users" = list("IT / TECHNOLOGY");
"threshold" = 50;
                """)
        finally:
            f.close()
        self.gitcommand(["add", "espinfo" + self.template_extension],
                        cwd=personalitydir)
        self.gitcommand(["commit", "-a", "-m",
                         "added personality utpersonality/dev"],
                        cwd=sandboxdir)

    def testaddesxserverpersonality(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("vmhost", "personality",
                                      "vulcan-1g-desktop-prod", "espinfo",
                                      sandbox="utsandbox")
        personalitydir = os.path.dirname(template)
        if not os.path.exists(personalitydir):
            os.makedirs(personalitydir)
        with open(template, 'w') as f:
            f.writelines(
                """structure template personality/vulcan-1g-desktop-prod/espinfo;

"description" = "Virtualisation Host running Server VMs";
"class" = "INFRASTRUCTURE";
"infrafunction" = "EUC-VMWARE";
"systemgrn" = list("grn:/ms/ei/windows/VMWare/ESX");
"function" = "production";
"users" = list("IT / TECHNOLOGY");
                """)
        self.gitcommand(["add", "espinfo" + self.template_extension],
                        cwd=personalitydir)
        template = self.template_name("vmhost", "personality",
                                      "vulcan-1g-desktop-prod", "windows",
                                      sandbox="utsandbox")
        with open(template, 'w') as f:
            f.writelines(
                """structure template personality/vulcan-1g-desktop-prod/windows;

"windows" = list(
                nlist("day", "Fri", "start", "23:00", "duration", 48),
);
                """)
        self.gitcommand(["add", "windows" + self.template_extension],
                        cwd=personalitydir)
        self.gitcommand(["commit", "-a", "-m",
                         "added personality vulcan-1g-desktop-prod"],
                         cwd=sandboxdir)

    def testaddutmedium(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("hardware", "machine", "utvendor",
                                      "utmedium", sandbox="utsandbox")
        modeldir = os.path.dirname(template)
        if not os.path.exists(modeldir):
            os.makedirs(modeldir)
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template hardware/machine/utvendor/utmedium;

"manufacturer" = "utvendor";
"model" = "utmedium";
"template_name" = "utmedium";
                """)
        finally:
            f.close()
        self.gitcommand(["add", "utmedium" + self.template_extension],
                        cwd=modeldir)
        self.gitcommand(["commit", "-a", "-m", "added model utmedium"],
                        cwd=sandboxdir)

    def testaddutccissmodel(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("hardware", "machine", "hp",
                                      "utccissmodel", sandbox="utsandbox")
        modeldir = os.path.dirname(template)
        if not os.path.exists(modeldir):
            os.makedirs(modeldir)
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template hardware/machine/hp/utccissmodel;

"manufacturer" = "hp";
"model" = "utccissmodel";
"template_name" = "utccissmodel";
                """)
        finally:
            f.close()
        self.gitcommand(["add", "utccissmodel" + self.template_extension],
                        cwd=modeldir)
        self.gitcommand(["commit", "-a", "-m", "added model utccissmodel"],
                        cwd=sandboxdir)

    def testaddutcpu(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("hardware", "cpu", "intel",
                                      "utcpu", sandbox="utsandbox")
        cpudir = os.path.dirname(template)
        if not os.path.exists(cpudir):
            os.makedirs(cpudir)
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template hardware/cpu/intel/utcpu;

"manufacturer" = "Intel";
"vendor" = "Intel";
"model" = "utcpu";
"speed" = 1000*MHz;
"arch" = "x86_64";
"cores" = 1;
                """)
        finally:
            f.close()
        self.gitcommand(["add", "utcpu" + self.template_extension], cwd=cpudir)
        self.gitcommand(["commit", "-a", "-m", "added cpu utcpu"],
                        cwd=sandboxdir)

    def testaddutvirt(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.template_name("hardware", "nic", "utvirt",
                                      "default", sandbox="utsandbox")
        modeldir = os.path.dirname(template)
        if not os.path.exists(modeldir):
            os.makedirs(modeldir)
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template hardware/nic/utvirt/default;

"boot"   = false;
"media"  = "Ethernet";
"name"   = "Generic Virt Interface";
                """)
        finally:
            f.close()
        self.gitcommand(["add", "default" + self.template_extension],
                        cwd=modeldir)
        self.gitcommand(["commit", "-a", "-m", "added model utvirt/default"],
                        cwd=sandboxdir)

    def testaddesxcluster(self):
        templates = {}
        templates['config'] = """
template personality/generic/config;

variable PERSONALITY = "generic";
include { "personality/config" };
"""
        templates['espinfo'] = """
structure template personality/generic/espinfo;

"description" = "Generic ESX Cluster";
"class" = "INFRASTRUCTURE";
"function" = "production";
"""
        templates['windows'] = """
structure template personality/generic/windows;

"windows" = list( nlist("day", "Fri", "start", "23:00", "duration", 48), );
"""
        sandboxdir = os.path.join(self.sandboxdir, 'utsandbox')
        for (name, contents) in templates.items():
            template = self.template_name("esx_cluster", "personality",
                                          "generic", name, sandbox="utsandbox")
            if not os.path.exists(os.path.dirname(template)):
                os.makedirs(os.path.dirname(template))
            with open(template, 'w') as f:
                f.writelines(contents)
            self.gitcommand(["add", template], cwd=sandboxdir)
        self.gitcommand(["commit", "-a", "-m", "added generic esx_cluster"],
                        cwd=sandboxdir)

    def testaddesxdesktop(self):
        templates = {}
        templates['config'] = """
template personality/vulcan-1g-desktop-prod/config;

variable PERSONALITY = "vulcan-1g-desktop-prod";
include { "personality/config" };
"""
        templates['espinfo'] = """
structure template personality/vulcan-1g-desktop-prod/espinfo;

"description" = "ESX Cluster for virtual desktops";
"class" = "INFRASTRUCTURE";
"function" = "production";
"""
        templates['windows'] = """
structure template personality/vulcan-1g-desktop-prod/windows;

"windows" = list( nlist("day", "Fri", "start", "23:00", "duration", 48), );
"""
        sandboxdir = os.path.join(self.sandboxdir, 'utsandbox')
        for (name, contents) in templates.items():
            template = self.template_name('esx_cluster', 'personality',
                                          'vulcan-1g-desktop-prod', name,
                                          sandbox="utsandbox")
            if not os.path.exists(os.path.dirname(template)):
                os.makedirs(os.path.dirname(template))
            with open(template, 'w') as f:
                f.writelines(contents)
            self.gitcommand(["add", template], cwd=sandboxdir)
        self.gitcommand(["commit", "-a", "-m", "added vulcan-1g-desktop-prod files"],
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

        # Skip the last commit
        sandboxdir = os.path.join(self.sandboxdir, "rebasetest")
        self.gitcommand(["reset", "--hard", "HEAD^"], cwd=sandboxdir)

        # Add some new content
        with open(os.path.join(sandboxdir, "TEST"), "w") as f:
            f.writelines(["Added test file"])
        self.gitcommand(["add", "TEST"], cwd=sandboxdir)
        self.gitcommand(["commit", "-m", "Added test file"], cwd=sandboxdir)

        # Try to publish it
        command = ["publish", "--sandbox", "rebasetest"]
        out = self.badrequesttest(command, env=self.gitenv(), cwd=sandboxdir,
                                  ignoreout=True)
        # This string comes from git, so it may change if git is upgraded
        self.matchoutput(out, "non-fast-forward", command)

        # Publish with rebasing enabled
        command.append("--rebase")
        self.ignoreoutputtest(command, env=self.gitenv(), cwd=sandboxdir)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPublishSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
