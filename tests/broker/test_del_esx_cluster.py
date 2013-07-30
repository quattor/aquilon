#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del esx cluster command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelESXCluster(TestBrokerCommand):

    def testdelutecl1(self):
        command = ["del_esx_cluster", "--cluster=utecl1"]
        self.successtest(command)

    def testverifydelutecl1(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        self.notfoundtest(command)

    def testdelutecl2(self):
        command = ["del_esx_cluster", "--cluster=utecl2"]
        self.successtest(command)

    def testverifydelutecl2(self):
        command = ["show_esx_cluster", "--cluster=utecl2"]
        self.notfoundtest(command)

    def testdelutecl3(self):
        command = ["del_esx_cluster", "--cluster=utecl3"]
        self.successtest(command)

    def testverifydelutecl3(self):
        command = ["show_esx_cluster", "--cluster=utecl3"]
        self.notfoundtest(command)

    def testdelutecl4(self):
        command = ["del_esx_cluster", "--cluster=utecl4"]
        self.successtest(command)

    def testverifydelutecl4(self):
        command = ["show_esx_cluster", "--cluster=utecl4"]
        self.notfoundtest(command)

    def testdelutmc4(self):
        for i in range(5, 11):
            command = ["del_esx_cluster", "--cluster=utecl%d" % i]
            self.successtest(command)

    def testdelutmc5(self):
        self.successtest(["del_esx_cluster", "--cluster=utecl11"])
        self.successtest(["del_esx_cluster", "--cluster=npecl11"])

    def testdelutmc6(self):
        self.successtest(["del_esx_cluster", "--cluster=utecl12"])
        self.successtest(["del_esx_cluster", "--cluster=npecl12"])

    def testdelutmc7(self):
        self.successtest(["del_esx_cluster", "--cluster=utecl13"])

    def testdelsandboxmc(self):
        self.successtest(["del_esx_cluster", "--cluster=sandboxcl1"])

    def testverifyall(self):
        command = ["show_esx_cluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "ESX Cluster: utecl", command)

    def testdelnotfound(self):
        command = ["del_esx_cluster", "--cluster=esx_cluster-does-not-exist"]
        self.notfoundtest(command)

    def verifyplenaryclusterclient(self):
        for i in range(1, 5):
            cluster = "utecl%s" % i
            dir = os.path.join(self.config.get("broker", "plenarydir"),
                               "cluster", cluster)
            self.failIf(os.path.exists(dir),
                        "Plenary directory '%s' still exists" % dir)
            plenary = self.build_profile_name("clusters", cluster,
                                              domain="unittest")
            self.failIf(os.path.exists(plenary),
                        "Plenary file '%s' still exists" % plenary)

    def verifyprofileclusterclient(self):
        profilesdir = self.config.get("broker", "profilesdir")
        for i in range(1, 5):
            cluster = "utecl%s" % i
            profile = os.path.join(profilesdir, "clusters", cluster + ".xml")
            self.failIf(os.path.exists(profile),
                        "Profile file '%s' still exists" % profile)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
