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
"""Module for testing the manage command."""


import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestManage(TestBrokerCommand):

    def verify_buildfiles(self, domain, object,
                          want_exist=True, command="manage"):
        qdir = self.config.get("broker", "quattordir")
        domaindir = os.path.join(qdir, "build", "xml", domain)
        xmlfile = os.path.join(domaindir, object + ".xml")
        depfile = os.path.join(domaindir, object + ".xml.dep")
        builddir = self.config.get("broker", "builddir")
        profile = os.path.join(builddir, "domains", domain, "profiles",
                               object + ".tpl")
        for f in [xmlfile, depfile, profile]:
            if want_exist:
                self.failUnless(os.path.exists(f),
                                "Expecting %s to exist before running %s." %
                                (f, command))
            else:
                self.failIf(os.path.exists(f),
                            "Not expecting %s to exist after running %s." %
                            (f, command))

    def testmanageunittest02(self):
        self.verify_buildfiles("unittest", "unittest02.one-nyp.ms.com",
                               want_exist=True)
        user = self.config.get("unittest", "user")
        self.noouttest(["manage", "--hostname", "unittest02.one-nyp.ms.com",
                        "--sandbox", "%s/changetest1" % user])
        self.verify_buildfiles("unittest", "unittest02.one-nyp.ms.com",
                               want_exist=False)

    def testverifymanageunittest02(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "Sandbox: %s/changetest1" % user, command)

    def testmanageserver1(self):
        self.noouttest(["manage", "--hostname", "server1.aqd-unittest.ms.com",
                        "--domain", "unittest"])

    def testverifymanageserver1(self):
        command = "show host --hostname server1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: server1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Domain: unittest", command)

    def testverifycleanup(self):
        basedir = self.config.get("broker", "basedir")
        command = [basedir,
                   "-name", "unittest02.one-nyp.ms.com*",
                   "-path", "*/unittest/*"]
        # basedir may contain the string ".../unittest/..."
        out = ["BASEDIR" + name[len(basedir):] for name in
               self.findcommand(command)]
        self.matchclean(" ".join(out), "/unittest/",
                        "find %s" % " ".join(command))

    def testmanageunittest00(self):
        self.verify_buildfiles("unittest", "unittest00.one-nyp.ms.com",
                               want_exist=True)
        user = self.config.get("unittest", "user")
        self.noouttest(["manage", "--hostname", "unittest00.one-nyp.ms.com",
                        "--sandbox", "%s/changetest2" % user])
        self.verify_buildfiles("unittest", "unittest00.one-nyp.ms.com",
                               want_exist=False)

    def testverifymanageunittest00(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Sandbox: %s/changetest2" % user, command)

    def testfailmanagevmhost(self):
        user = self.config.get("unittest", "user")
        command = ["manage", "--hostname", "evh1.aqd-unittest.ms.com",
                   "--sandbox", "%s/changetest1" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cluster nodes must be managed at the cluster level",
                         command)

    def testmanagemissingcluster(self):
        user = self.config.get("unittest", "user")
        command = ["manage", "--cluster", "cluster-does-not-exist",
                   "--sandbox", "%s/changetest1" % user]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

    def testmanagecluster(self):
        self.verify_buildfiles("unittest", "clusters/utecl1", want_exist=True)
        user = self.config.get("unittest", "user")
        command = ["manage", "--cluster", "utecl1",
                   "--sandbox", "%s/changetest1" % user]
        self.noouttest(command)
        self.verify_buildfiles("unittest", "clusters/utecl1", want_exist=False)

    def testverifymanagecluster(self):
        user = self.config.get("unittest", "user")
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Sandbox: %s/changetest1" % user, command)

        command = ["search_host", "--cluster=utecl1"]
        out = self.commandtest(command)
        members = out.splitlines()
        members.sort()
        self.failUnless(members, "No hosts in output of %s." % command)

        command = ["search_host", "--cluster=utecl1",
                   "--sandbox=%s/changetest1" % user]
        out = self.commandtest(command)
        aligned = out.splitlines()
        aligned.sort()
        self.failUnlessEqual(members, aligned,
                             "Not all utecl1 cluster members (%s) are in "
                             "sandbox changetest1 (%s)." % (members, aligned))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
