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
"""Module for testing the put domain command."""


from __future__ import with_statement

import os
import sys
import unittest
from subprocess import Popen

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestPutDomain(TestBrokerCommand):

    def testmakechange(self):
        template = os.path.join(self.scratchdir, "changetest1", "aquilon",
                "archetype", "base.tpl")
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
                cwd=os.path.join(self.scratchdir, "changetest1"))

    def testputchangetest1domain(self):
        self.ignoreoutputtest(["put", "--domain", "changetest1"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "changetest1"))
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest1")))

    def testverifychangetest1(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.scratchdir, "changetest1")),
                  stdout=1, stderr=2)
        rc = p.wait()
        self.ignoreoutputtest(["get", "--domain", "changetest1"],
                              cwd=self.scratchdir)
        self.failUnless(os.path.exists(os.path.join(self.scratchdir,
                                                    "changetest1")))
        template = os.path.join(self.scratchdir, "changetest1", "aquilon",
                                "archetype", "base.tpl")
        self.failUnless(os.path.exists(template),
                        "aq get did not retrive '%s'" % template)
        with open(template) as f:
            contents = f.readlines()
        self.failUnlessEqual(contents[-1], "#Added by unittest\n")

    def testaddsiteut(self):
        repodir = os.path.join(self.scratchdir, "unittest")
        if os.path.exists(os.path.join(repodir, "site")):
            sitedir = os.path.join(repodir, "site")
        else:
            sitedir = os.path.join(repodir, "aquilon", "site")
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
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddutsi1(self):
        """utsi1 = unit test service instance 1"""
        svcdir = os.path.join(self.scratchdir, "unittest", "service",
                "utsvc", "utsi1", "client")
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
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddutsi2(self):
        """utsi1 = unit test service instance 2"""
        svcdir = os.path.join(self.scratchdir, "unittest", "service",
                "utsvc", "utsi2", "client")
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
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddutpersonality(self):
        personalitydir = os.path.join(self.scratchdir, "unittest", "aquilon",
                                      "personality", "utpersonality")
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
                         cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddesxserverpersonality(self):
        personalitydir = os.path.join(self.scratchdir, "unittest", "vmhost",
                                      "personality", "esx_server")
        if not os.path.exists(personalitydir):
            os.makedirs(personalitydir)
        template = os.path.join(personalitydir, "espinfo.tpl")
        with open(template, 'w') as f:
            f.writelines(
                """structure template personality/esx_server/espinfo;

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
                """structure template personality/esx_server/windows;

"windows" = list(
                nlist("day", "Fri", "start", "23:00", "duration", 48),
);
                """)
        self.gitcommand(["add", "windows.tpl"], cwd=personalitydir)
        self.gitcommand(["commit", "-a", "-m",
                         "added personality esx_server"],
                         cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddutmedium(self):
        modeldir = os.path.join(self.scratchdir, "unittest", "hardware",
                                "machine", "utvendor")
        if not os.path.exists(modeldir):
            os.makedirs(modeldir)
        template = os.path.join(modeldir, "utmedium.tpl")
        f = open(template, 'w')
        try:
            f.writelines(
                """structure template hardware/machine/utvendor/utmedium;

"manufacturer" = "utvendor";
"model" = "utmedium";
                """)
        finally:
            f.close()
        self.gitcommand(["add", "utmedium.tpl"], cwd=modeldir)
        self.gitcommand(["commit", "-a", "-m",
                         "added model utmedium"],
                         cwd=os.path.join(self.scratchdir, "unittest"))

    def testputunittestdomain(self):
        self.ignoreoutputtest(["put", "--domain", "unittest"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "unittest"))
        repodir = os.path.join(self.config.get("broker", "templatesdir"),
                               "unittest")
        if os.path.exists(os.path.join(repodir, "site")):
            sitedir = os.path.join(repodir, "site")
        else:
            sitedir = os.path.join(repodir, "aquilon", "site")
        self.assert_(os.path.exists(os.path.join(sitedir, "americas",
                                                 "ny", "ut", "config.tpl")))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPutDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

