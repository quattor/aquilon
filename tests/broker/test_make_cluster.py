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
"""Module for testing the make cluster command."""

import os
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestMakeCluster(VerifyNotificationsMixin, TestBrokerCommand):

    def testmakeutecl1(self):
        basetime = datetime.now()
        command = ["make_cluster", "--cluster", "utecl1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "ESX Cluster utecl1 adding binding for "
                         "service instance esx_management_server",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utecl1%s" % self.profile_suffix)))

        self.failUnless(os.path.exists(
            self.build_profile_name("clusters", "utecl1", domain="unittest")))

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
        basetime = datetime.now()
        command = ["make_cluster", "--cluster", "utecl2"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "ESX Cluster utecl2 adding binding for "
                         "service instance esx_management_server",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utecl2%s" % self.profile_suffix)))

        self.failUnless(os.path.exists(
            self.build_profile_name("clusters", "utecl2", domain="unittest")))

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
