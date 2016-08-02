#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin
from clustertest import ClusterTestMixin


class TestMakeCluster(VerifyNotificationsMixin, ClusterTestMixin,
                      TestBrokerCommand):

    def test_100_make_utecl1(self):
        basetime = datetime.now()
        command = ["make_cluster", "--cluster", "utecl1"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "ESX Cluster utecl1 adding binding for "
                         "service instance esx_management_server",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

        self.assertTrue(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utecl1%s" % self.xml_suffix)))

        self.assertTrue(os.path.exists(
            self.build_profile_name("clusters", "utecl1", domain="unittest")))

    def test_105_cat_utecl1(self):
        obj_cmd, obj, data_cmd, data = self.verify_cat_clusters("utecl1",
                                                                "esx_cluster",
                                                                "vulcan-10g-server-prod",
                                                                metacluster="utmc1")
        self.searchoutput(obj,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          obj_cmd)

        self.matchoutput(data, '"system/cluster/down_hosts_threshold" = 2;',
                         data_cmd)
        self.matchoutput(data, '"system/cluster/down_maint_threshold" = 2;',
                         data_cmd)
        self.matchclean(data, '"system/cluster/down_hosts_as_percent"', data_cmd)
        self.matchclean(data, '"system/cluster/down_maint_as_percent"', data_cmd)
        self.matchclean(data, '"system/cluster/down_hosts_percent"', data_cmd)
        self.matchclean(data, '"system/cluster/down_maint_percent"', data_cmd)

    def test_105_verify_svc(self):
        # The cluster may use either the ut.a or ut.b instance, so we need to
        # check which one was choosen
        command = ["show_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service '
                              r'esx_management_server Instance (\S+)',
                              command)
        instance = m.group(1)
        other = instance == 'ut.a' and 'ut.b' or 'ut.a'

        command = ["cat", "--service", "esx_management_server",
                   "--instance", instance, "--server"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"cluster_clients" = list\([^)]*"utecl1"[^)]*\);',
                          command)

        command = ["cat", "--service", "esx_management_server",
                   "--instance", other, "--server"]
        out = self.commandtest(command)
        self.matchclean(out, '"utecl1"', command)

    def test_110_add_allowed_personality(self):
        self.successtest(["add_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=vulcan-10g-server-prod",
                          "--cluster", "utecl1"])

        self.successtest(["add_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=generic",
                          "--cluster", "utecl1"])

        self.successtest(["make_cluster", "--cluster", "utecl1"])

        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))

        self.searchoutput(out,
                          r'"system/cluster/allowed_personalities" = list\(\s*' +
                          '"vmhost/generic",' + r'\s*' +
                          '"vmhost/vulcan-10g-server-prod"' + r'\s*\);',
                          command)

        self.successtest(["del_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=generic",
                          "--cluster=utecl1"])

        self.successtest(["del_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=vulcan-10g-server-prod",
                          "--cluster", "utecl1"])

    def test_120_make_utecl2(self):
        basetime = datetime.now()
        command = ["make_cluster", "--cluster", "utecl2"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "ESX Cluster utecl2 adding binding for "
                         "service instance esx_management_server",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

        self.assertTrue(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utecl2%s" % self.xml_suffix)))

        self.assertTrue(os.path.exists(
            self.build_profile_name("clusters", "utecl2", domain="unittest")))

    def test_125_verify_utecl2(self):
        obj_cmd, obj, data_cmd, data = self.verify_cat_clusters("utecl2",
                                                                "esx_cluster",
                                                                "vulcan-10g-server-prod",
                                                                metacluster="utmc1")

        self.searchoutput(obj,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          obj_cmd)

        self.matchoutput(data, '"system/cluster/down_hosts_threshold" = 1;',
                         data_cmd)

    def test_130_make_utgrid1(self):
        command = "make_cluster --cluster utgrid1"
        self.successtest(command.split(" "))

    def test_135_verify_utgrid1(self):
        _, _, data_cmd, data = self.verify_cat_clusters("utgrid1",
                                                        "gridcluster", "hadoop")

        self.matchoutput(data, '"system/cluster/down_hosts_threshold" = 0;',
                         data_cmd)
        self.matchoutput(data, '"system/cluster/down_maint_threshold" = 0;',
                         data_cmd)
        self.matchoutput(data, '"system/cluster/down_hosts_as_percent" = true;',
                         data_cmd)
        self.matchoutput(data, '"system/cluster/down_maint_as_percent" = true;',
                         data_cmd)
        self.matchoutput(data, '"system/cluster/down_hosts_percent" = 5;',
                         data_cmd)
        self.matchoutput(data, '"system/cluster/down_maint_percent" = 6;',
                         data_cmd)
        self.matchclean(data, '/system/cluster/max_hosts', data_cmd)

    def test_140_make_utvcs1(self):
        command = "make_cluster --cluster utvcs1"
        self.successtest(command.split(" "))

    def test_145_verify_cat_utvcs1(self):
        _, _, data_cmd, data = self.verify_cat_clusters("utvcs1", "hacluster",
                                                        "hapersonality")

        self.matchoutput(data, '"system/cluster/down_hosts_threshold" = 0;',
                         data_cmd)
        self.matchclean(data, "down_maint_threshold", data_cmd)
        self.matchclean(data, "down_hosts_as_percent", data_cmd)
        self.matchclean(data, "down_maint_as_percent", data_cmd)
        self.matchclean(data, "down_hosts_percent", data_cmd)
        self.matchclean(data, "down_maint_percent", data_cmd)

    def test_150_make_utmc4(self):
        for i in range(5, 11):
            command = ["make_cluster", "--cluster", "utecl%d" % i]
            self.statustest(command)

    def test_151_make_utmc7(self):
        command = ["make_cluster", "--cluster", "utecl11"]
        self.statustest(command)

    def test_152_make_utmc8(self):
        self.statustest(["make_cluster", "--metacluster", "utmc8"])

        command = ["cat", "--metacluster", "utmc8", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template clusterdata/utmc8;", command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc8";', command)
        self.matchoutput(out, '"system/metacluster/type" = "meta";', command)
        self.searchoutput(out,
                          r'"system/metacluster/members" = list\(\s*'
                          r'"utecl12",\s*'
                          r'"utecl13"\s*'
                          r'\);',
                          command)
        self.matchoutput(out, '"system/build" = "build";', command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/location" = "ut.ny.na";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/continent" = "na";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/country" = "us";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/city" = "ny";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/campus" = "ny";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/building" = "ut";',
                         command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as1/config"));',
                         command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as2/config"));',
                         command)

    def test_153_make_utmc9(self):
        self.statustest(["make_cluster", "--cluster", "utecl14"])
        self.statustest(["make_cluster", "--cluster", "utecl15"])

    def test_200_missing_cluster(self):
        command = ["make_cluster", "--cluster=cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
