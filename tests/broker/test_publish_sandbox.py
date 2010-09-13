#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Module for testing the publish command."""


import os
import unittest
from subprocess import Popen

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPublishSandbox(TestBrokerCommand):

    def testmakechange(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        template = os.path.join(sandboxdir, "aquilon", "archetype", "base.tpl")
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
        self.failUnless(sandboxdir)
        template = os.path.join(sandboxdir, "aquilon", "archetype", "base.tpl")
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
        template = os.path.join(utdir, "config.tpl")
        f = open(template, 'w')
        try:
            f.writelines("template site/americas/ny/ut/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config.tpl"], cwd=utdir)
        self.gitcommand(["commit", "-a", "-m", "added building ut"],
                        cwd=sandboxdir)

    def testaddutsi1(self):
        """utsi1 = unit test service instance 1"""
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        svcdir = os.path.join(sandboxdir, "service", "utsvc", "utsi1",
                              "client")
        if not os.path.exists(svcdir):
            os.makedirs(svcdir)
        template = os.path.join(svcdir, "config.tpl")
        f = open(template, 'w')
        try:
            f.writelines("template service/utsvc/utsi1/client/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config.tpl"], cwd=svcdir)
        self.gitcommand(["commit", "-a", "-m",
                         "added unit test service instance 1"],
                        cwd=sandboxdir)

    def testaddutsi2(self):
        """utsi1 = unit test service instance 2"""
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        svcdir = os.path.join(sandboxdir, "service", "utsvc", "utsi2",
                              "client")
        if not os.path.exists(svcdir):
            os.makedirs(svcdir)
        template = os.path.join(svcdir, "config.tpl")
        f = open(template, 'w')
        try:
            f.writelines("template service/utsvc/utsi2/client/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config.tpl"], cwd=svcdir)
        self.gitcommand(["commit", "-a", "-m",
                         "added unit test service instance 2"],
                        cwd=sandboxdir)

    def testaddutpersonality(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        personalitydir = os.path.join(sandboxdir, "aquilon", "personality",
                                      "utpersonality")
        if not os.path.exists(personalitydir):
            os.makedirs(personalitydir)
        template = os.path.join(personalitydir, "espinfo.tpl")
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template personality/utpersonality/espinfo;

"name" = "utpersonality";
"description" = "regression test personality";
"class" = "INFRASTRUCTURE";
"infrafunction" = "Sapphire-INV";
"function" = "development";
"users" = list("IT / TECHNOLOGY");
"threshold" = 50;
                """)
        finally:
            f.close()
        self.gitcommand(["add", "espinfo.tpl"], cwd=personalitydir)
        self.gitcommand(["commit", "-a", "-m",
                         "added personality utpersonality"],
                        cwd=sandboxdir)

    def testaddesxserverpersonality(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        personalitydir = os.path.join(sandboxdir, "vmhost",
                                      "personality", "esx_desktop")
        if not os.path.exists(personalitydir):
            os.makedirs(personalitydir)
        template = os.path.join(personalitydir, "espinfo.tpl")
        with open(template, 'w') as f:
            f.writelines(
                """structure template personality/esx_desktop/espinfo;

"description" = "Virtualisation Host running Server VMs";
"class" = "INFRASTRUCTURE";
"infrafunction" = "EUC-VMWARE";
"systemgrn" = list("grn:/ms/ei/windows/VMWare/ESX");
"function" = "production";
"users" = list("IT / TECHNOLOGY");
                """)
        self.gitcommand(["add", "espinfo.tpl"], cwd=personalitydir)
        template = os.path.join(personalitydir, "windows.tpl")
        with open(template, 'w') as f:
            f.writelines(
                """structure template personality/esx_desktop/windows;

"windows" = list(
                nlist("day", "Fri", "start", "23:00", "duration", 48),
);
                """)
        self.gitcommand(["add", "windows.tpl"], cwd=personalitydir)
        self.gitcommand(["commit", "-a", "-m",
                         "added personality esx_desktop"],
                         cwd=sandboxdir)

    def testaddutmedium(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        modeldir = os.path.join(sandboxdir, "hardware", "machine", "utvendor")
        if not os.path.exists(modeldir):
            os.makedirs(modeldir)
        template = os.path.join(modeldir, "utmedium.tpl")
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
        self.gitcommand(["add", "utmedium.tpl"], cwd=modeldir)
        self.gitcommand(["commit", "-a", "-m", "added model utmedium"],
                        cwd=sandboxdir)

    def testaddutccissmodel(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        modeldir = os.path.join(sandboxdir, "hardware", "machine", "hp")
        if not os.path.exists(modeldir):
            os.makedirs(modeldir)
        template = os.path.join(modeldir, "utccissmodel.tpl")
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
        self.gitcommand(["add", "utccissmodel.tpl"], cwd=modeldir)
        self.gitcommand(["commit", "-a", "-m", "added model utccissmodel"],
                        cwd=sandboxdir)

    def testaddutcpu(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        cpudir = os.path.join(sandboxdir, "hardware", "cpu", "intel")
        if not os.path.exists(cpudir):
            os.makedirs(cpudir)
        template = os.path.join(cpudir, "utcpu.tpl")
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template hardware/cpu/intel/utcpu;

"manufacturer" = "Intel";
"vendor" = "Intel";
"model" = "utcpu";
"speed" = "1000*MHz";
"arch" = "x86_64";
                """)
        finally:
            f.close()
        self.gitcommand(["add", "utcpu.tpl"], cwd=cpudir)
        self.gitcommand(["commit", "-a", "-m", "added cpu utcpu"],
                        cwd=sandboxdir)

    def testpublishutsandbox(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.ignoreoutputtest(["publish", "--branch", "utsandbox"],
                              env=self.gitenv(), cwd=sandboxdir)
        # FIXME: verify that changes made it to unittest


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPublishSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
