#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the del cluster command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelCluster(TestBrokerCommand):

    def test_100_delutgrid1(self):
        command = ["del_cluster", "--cluster=utgrid1"]
        self.successtest(command)

    def test_100_verifydelutgrid1(self):
        command = ["show_cluster", "--cluster=utgrid1"]
        self.notfoundtest(command)

    def test_100_verifyall(self):
        command = ["show_cluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "utgrid", command)

    def test_100_delnotfound(self):
        command = ["del_cluster", "--cluster=grid_cluster-does-not-exist"]
        self.notfoundtest(command)

    def test_100_verifyplenaryclusterclient(self):
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "cluster", "utgrid1")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)
        plenary = self.build_profile_name("clusters", "utgrid1",
                                          domain="unittest")
        self.failIf(os.path.exists(plenary),
                    "Plenary file '%s' still exists" % plenary)

    def test_200_delutvcs1(self):
        command = ["del_cluster", "--cluster=utvcs1"]
        self.successtest(command)

    def test_200_verifydelutvcs1(self):
        command = ["show_cluster", "--cluster=utvcs1"]
        self.notfoundtest(command)

        profile = os.path.join(self.config.get("broker", "profilesdir"),
                               "clusters", "utvcs1.xml")
        self.failIf(os.path.exists(profile),
                    "Profile file '%s' still exists" % profile)

    def test_200_verifyall(self):
        command = ["show_cluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "utvcs", command)

    def test_300_delutstorage1(self):
        command = ["del_cluster", "--cluster=utstorage1"]
        self.successtest(command)

    def test_300_verifydelutstorage1(self):
        command = ["show_cluster", "--cluster=utstorage1"]
        self.notfoundtest(command)

    def test_300_delutstorage2(self):
        command = ["del_cluster", "--cluster=utstorage2"]
        self.successtest(command)

    def test_300_verifydelutstorage2(self):
        command = ["show_cluster", "--cluster=utstorage2"]
        self.notfoundtest(command)

    def test_300_delutstorages2(self):
        command = ["del_cluster", "--cluster=utstorages2"]
        self.successtest(command)

    def test_300_verifydelutstorages2(self):
        command = ["show_cluster", "--cluster=utstorages2"]
        self.notfoundtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
