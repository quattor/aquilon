#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the add cluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestAddCluster(PersonalityTestMixin, TestBrokerCommand):

    def test_10_add_metrocluster(self):
        self.create_personality("storagecluster", "metrocluster",
                                environment="prod")

    def test_10_add_utvcs1(self):
        command = ["add_cluster", "--cluster=utvcs1",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=hapersonality"]
        self.noouttest(command)

    def test_11_verify_utvcs1(self):
        command = "show cluster --cluster utvcs1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.getint("archetype_hacluster",
                                         "max_members_default")
        self.output_equals(out, """
            High Availability Cluster: utvcs1
              Member Location Constraint:
                Building: ut
                  Fullname: Unittest-building
                  Address: unittest address
                  Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny]
              Max members: %s
              Down Hosts Threshold: 0
              Build Status: build
              Cluster Personality: hapersonality Archetype: hacluster
                Environment: dev
                Owned by GRN: grn:/ms/ei/aquilon/aqd
              Domain: unittest
            """ % default_max, command)

    def test_12_verify_cat_utvcs1_client(self):
        command = ["cat", "--cluster", "utvcs1", "--client"]
        out = self.commandtest(command)
        self.searchoutput(out, r'"/system/cluster/name" = "utvcs1";', command)
        self.searchoutput(out,
                          r'include { if_exists\("features/" \+ value\("/system/archetype/name"\) \+ "/hacluster/hapersonality/config"\) };',
                          command)

    def test_20_fail_add_existing(self):
        command = ["add_cluster", "--cluster=utvcs1",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=hapersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cluster utvcs1 already exists", command)

    def test_20_verify_showall(self):
        command = "show cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utvcs1", command)

    def test_20_notfound_cluster(self):
        command = "show cluster --cluster cluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_20_fail_nomanage(self):
        command = ["add_cluster", "--cluster=utvcs2",
                   "--building=ut",
                   "--domain=nomanage", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=hapersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Adding clusters to domain nomanage "
                         "is not allowed.", command)

    def test_30_verify_plenary_ha_clusterclient(self):
        cluster = "utvcs1"
        plenary = self.plenary_name("cluster", cluster, "client")
        with open(plenary) as f:
            contents = f.read()
        self.matchoutput(contents,
                         '"/system/cluster/name" = "%s";' % cluster,
                         "read %s" % plenary)

    def test_40_add_utgrid1(self):
        command = ["add_cluster", "--cluster=utgrid1",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=5%",
                   "--maint_threshold=6%",
                   "--archetype=gridcluster", "--personality=hadoop"]
        self.noouttest(command)

    def test_41_verify_utgrid1(self):
        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            Grid Cluster: utgrid1
              Member Location Constraint:
                Building: ut
                  Fullname: Unittest-building
                  Address: unittest address
                  Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny]
              Max members: unlimited
              Down Hosts Threshold: 0 (5%)
              Maintenance Threshold: 0 (6%)
              Build Status: build
              Cluster Personality: hadoop Archetype: gridcluster
                Environment: dev
                Owned by GRN: grn:/ms/ei/aquilon/aqd
              Domain: unittest
            """, command)

    def test_43_verifyshowutgrid1proto(self):
        command = ["show_cluster", "--cluster=utgrid1", "--format=proto"]
        cluster = self.protobuftest(command, expect=1)[0]
        self.assertEqual(cluster.name, "utgrid1")
        self.assertEqual(cluster.personality.archetype.name, "gridcluster")
        self.assertEqual(cluster.personality.archetype.cluster_type, "compute")
        self.assertEqual(cluster.domain.name, 'unittest')
        self.assertEqual(cluster.domain.type, cluster.domain.DOMAIN)
        self.assertEqual(cluster.sandbox_author, "")
        self.assertEqual(cluster.status, "build")
        self.assertEqual(cluster.location_constraint.name, "ut")
        self.assertEqual(cluster.location_constraint.location_type, "building")
        self.assertEqual(cluster.max_members, 0)
        self.assertEqual(cluster.threshold, 5)
        self.assertEqual(cluster.threshold_is_percent, True)
        self.assertEqual(cluster.maint_threshold, 6)
        self.assertEqual(cluster.maint_threshold_is_percent, True)
        self.assertEqual(cluster.metacluster, "")
        self.assertEqual(cluster.virtual_switch.name, "")

    def test_44_verifyshowall(self):
        command = "show cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utgrid1", command)
        self.matchoutput(out, "utvcs1", command)

    def test_45_verifyshowallproto(self):
        command = "show cluster --all --format proto"
        clusters = self.protobuftest(command.split(" "))
        clusternames = set(msg.name for msg in clusters)
        for clustername in ("utgrid1", "utvcs1"):
            self.assertIn(clustername, clusternames)

    def test_45_verifyplenary_grid_clusterclient(self):
        plenary = self.plenary_name("cluster", "utgrid1", "client")
        with open(plenary) as f:
            contents = f.read()
        self.matchoutput(contents,
                         '"/system/cluster/name" = "utgrid1";',
                         "read %s" % plenary)

    def test_50_addutstorage1(self):
        # For this cluster, we'll use the default for buildstatus
        # to confirm it does the right thing
        command = ["add_cluster", "--cluster=utstorage1",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--maint_threshold=1",
                   "--archetype=storagecluster", "--personality=metrocluster"]
        self.noouttest(command)

    def test_51_verifyutstorage1(self):
        command = "show cluster --cluster utstorage1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Storage Cluster: utstorage1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Down Hosts Threshold: 0", command)
        self.matchoutput(out, "Maintenance Threshold: 1", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Cluster Personality: metrocluster Archetype: storagecluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_53_verifyshowutstorage1proto(self):
        command = ["show_cluster", "--cluster=utstorage1", "--format=proto"]
        cluster = self.protobuftest(command, expect=1)[0]
        self.assertEqual(cluster.name, "utstorage1")
        self.assertEqual(cluster.personality.archetype.name, "storagecluster")
        self.assertEqual(cluster.threshold, 0)
        self.assertEqual(cluster.threshold_is_percent, False)

    def test_54_addutstorage2(self):
        command = ["add_cluster", "--cluster=utstorage2",
                   "--building=ut",
                   "--buildstatus=build",
                   "--archetype=storagecluster", "--personality=metrocluster",
                   "--domain=unittest", "--down_hosts_threshold=1",
                   "--max_members=2",
                   "--comments=Some storage cluster comments"]
        self.noouttest(command)

    def test_55_verifyutstorage2(self):
        command = "show cluster --cluster utstorage2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Storage Cluster: utstorage2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 2", command)
        self.matchoutput(out, "Down Hosts Threshold: 1", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Personality: metrocluster Archetype: storagecluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Comments: Some storage cluster comments", command)

    def test_57_addutstorages2(self):
        command = ["add_cluster", "--cluster=utstorages2",
                   "--building=bu",
                   "--buildstatus=ready",
                   "--archetype=storagecluster", "--personality=metrocluster",
                   "--sandbox=%s/utsandbox" % self.user, "--down_hosts_threshold=1",
                   "--max_members=2",
                   "--comments=Test storage cluster for sandbox"]
        self.noouttest(command)

    def test_60_metacluster_name_conflict(self):
        command = ["add_metacluster", "--metacluster", "utvcs1",
                   "--domain", "unittest", "--building", "ut",
                   "--archetype", "metacluster",
                   "--personality", "metacluster"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Compute Cluster utvcs1 already exists.",
                         command)

    def test_70_add_camelcase(self):
        command = ["add_cluster", "--cluster=CaMeLcAsE",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=hapersonality"]
        self.noouttest(command)
        self.check_plenary_exists("clusterdata", "camelcase")
        self.check_plenary_gone("clusterdata", "CaMeLcAsE")
        self.check_plenary_exists("cluster", "camelcase", "client")
        self.check_plenary_gone("cluster", "CaMeLcAsE", "client")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
