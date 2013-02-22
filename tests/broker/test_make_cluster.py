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
"""Module for testing the make cluster command."""


import os
import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()


from brokertest import TestBrokerCommand


class TestMakeCluster(TestBrokerCommand):

    def testmakeutecl1(self):
        command = ["make_cluster", "--cluster", "utecl1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "ESX Cluster utecl1 adding binding for "
                         "service esx_management_server",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "sent 1 server notifications", command)

        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utecl1%s" % self.profile_suffix)))

        self.failUnless(os.path.exists(os.path.join(
            self.config.get("broker", "builddir"),
            "domains", "unittest", "profiles", "clusters",
            "utecl1.tpl")))

    def testverifycatutecl1(self):
        command = "cat --cluster=utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template clusters/utecl1;", command)
        self.searchoutput(out,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)

        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"system/cluster/name" = "utecl1";', command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc1";', command)
        self.matchclean(out, "resources/virtual_machine", command)

    def testverifycatutecl1_2(self):
        self.successtest(["add_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=vulcan-1g-desktop-prod",
                          "--cluster", "utecl1"])

        self.successtest(["add_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=generic",
                          "--cluster", "utecl1"])

        command = ["make_cluster", "--cluster", "utecl1"]
        (out, err) = self.successtest(command)

        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))

        self.searchoutput(out,
                          r'"system/cluster/allowed_personalities" = list\(\s*' +
                          '"vmhost/generic",' + r'\s*' +
                          '"vmhost/vulcan-1g-desktop-prod"' + r'\s*\);',
                          command)

        self.successtest(["del_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=generic",
                          "--cluster=utecl1"])

        self.successtest(["del_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=vulcan-1g-desktop-prod",
                          "--cluster", "utecl1"])

    def testverifygridcluster(self):
        command = "make_cluster --cluster utgrid1"
        (out, err) = self.successtest(command.split(" "))

        command = "cat --cluster=utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)

    def testverifyhacluster(self):
        command = "make_cluster --cluster utvcs1"
        (out, err) = self.successtest(command.split(" "))

        command = "cat --cluster=utvcs1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)

    def testmakeutecl2(self):
        command = ["make_cluster", "--cluster", "utecl2"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "ESX Cluster utecl2 adding binding for "
                         "service esx_management_server",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "sent 1 server notifications", command)

        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utecl2%s" % self.profile_suffix)))

        self.failUnless(os.path.exists(os.path.join(
            self.config.get("broker", "builddir"),
            "domains", "unittest", "profiles", "clusters",
            "utecl2.tpl")))

    def testverifycatutecl2(self):
        command = "cat --cluster=utecl2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template clusters/utecl2;", command)
        self.searchoutput(out,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)

        command = "cat --cluster=utecl2 --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"system/cluster/name" = "utecl2";', command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc1";', command)
        self.matchclean(out, "resources/virtual_machine", command)

    def testfailmissingcluster(self):
        command = ["make_cluster", "--cluster=cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found.",
                         command)

    def testmakeutmc4(self):
        for i in range(5, 11):
            command = ["make_cluster", "--cluster", "utecl%d" % i]
            (out, err) = self.successtest(command)

    def testmake_esx_bcp_clusters(self):
        for i in range(11, 13):
            self.successtest(["make_cluster", "--cluster", "utecl%d" % i])
            self.successtest(["make_cluster", "--cluster", "npecl%d" % i])

    def testmakeutmc7(self):
        for i in [13]:
            command = ["make_cluster", "--cluster", "utecl%d" % i]
            (out, err) = self.successtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
