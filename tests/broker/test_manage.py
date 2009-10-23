#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestManage(TestBrokerCommand):

    def testmanageunittest02(self):
        self.noouttest(["manage", "--hostname", "unittest02.one-nyp.ms.com",
            "--domain", "changetest1"])

    def testverifymanageunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "Domain: changetest1", command)

    def testverifycleanup(self):
        command = [self.config.get("broker", "basedir"),
                   "-name", "unittest02.one-nyp.ms.com*",
                   "-path", "*/unittest/*"]
        out = self.findcommand(command)
        self.matchclean("".join(out), "unittest",
                        "find %s" % " ".join(command))

    def testmanageunittest00(self):
        self.noouttest(["manage", "--hostname", "unittest00.one-nyp.ms.com",
            "--domain", "changetest2"])

    def testverifymanageunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Domain: changetest2", command)

    def testfailmanagevmhost(self):
        command = ["manage", "--hostname", "evh1.aqd-unittest.ms.com",
                   "--domain", "changetest1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "cluster nodes must be managed at the cluster level",
                         command)

    def testmanagemissingcluster(self):
        command = ["manage", "--cluster", "cluster-does-not-exist",
                   "--domain", "changetest1"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "cluster 'cluster-does-not-exist' not found",
                         command)

    def testmanagecluster(self):
        command = ["manage", "--cluster", "utecl1", "--domain", "changetest1"]
        self.noouttest(command)

    def testverifymanagecluster(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Domain: changetest1", command)

        command = ["search_host", "--cluster=utecl1"]
        out = self.commandtest(command)
        members = out.splitlines()
        members.sort()
        self.failUnless(members, "No hosts in output of %s." % command)

        command = ["search_host", "--cluster=utecl1", "--domain=changetest1"]
        out = self.commandtest(command)
        aligned = out.splitlines()
        aligned.sort()
        self.failUnlessEqual(members, aligned,
                             "Not all utecl1 cluster members (%s) are in "
                             "domain changetest1 (%s)." % (members, aligned))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

