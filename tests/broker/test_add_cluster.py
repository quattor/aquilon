#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Module for testing the add cluster command."""

import os
import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddCluster(TestBrokerCommand):

    def test_00_add_utvcs1(self):
        command = ["add_cluster", "--cluster=utvcs1",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--maint_threshold=1",
                   "--archetype=hacluster", "--personality=vcs-msvcs"]
        self.noouttest(command)

    def test_10_verify_utvcs1(self):
        command = "show cluster --cluster utvcs1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.get("broker",
                                      "hacluster_max_members_default")
        self.matchoutput(out, "High Availability Cluster: utvcs1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "Down Hosts Threshold: 0", command)
        self.matchoutput(out, "Maintenance Threshold: 1", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Personality: vcs-msvcs Archetype: hacluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_10_verify_cat_utvcs1(self):
        command = ["cat", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self._verify_cat_on_clusters("utvcs1", "vcs-msvcs", "compute", out, command)

    def test_20_fail_add_existing(self):
        command = ["add_cluster", "--cluster=utvcs1",
                   "--building=ut",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=vcs-msvcs"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cluster utvcs1 already exists", command)

    def test_20_verify_showall(self):
        command = "show cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "High Availability Cluster: utvcs1", command)

    def test_20_notfound_cluster(self):
        command = "show cluster --cluster cluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_30_verify_plenary_ha_clusterclient(self):
        cluster = "utvcs1"
        plenary = os.path.join(self.config.get("broker", "plenarydir"),
                               "cluster", cluster, "client.tpl")
        with open(plenary) as f:
            contents = f.read()
        self.matchoutput(contents,
                         '"/system/cluster/name" = "%s";' % cluster,
                         "read %s" % plenary)

    def test_40_add_utgrid1(self):
        command = ["add_cluster", "--cluster=utgrid1",
                   "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=5%",
                   "--archetype=gridcluster", "--personality=hadoop"]
        self.noouttest(command)

    def test_41_verify_utgrid1(self):
        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.get("broker",
                                      "gridcluster_max_members_default")
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Down Hosts Threshold: 0 (5%)", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Cluster Personality: hadoop Archetype: gridcluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_42_verifycatutgrid1(self):
        command = ["cat", "--cluster=utgrid1"]
        out = self.commandtest(command)
        self._verify_cat_on_clusters("utgrid1", "hadoop", "compute", out, command)

    def test_43_verifyshowutgrid1proto(self):
        command = ["show_cluster", "--cluster=utgrid1", "--format=proto"]
        out = self.commandtest(command)
        clus_list = self.parse_clusters_msg(out, 1)
        cluster = clus_list.clusters[0]
        self.failUnlessEqual(cluster.name, "utgrid1")
        self.failUnlessEqual(cluster.personality.archetype.name, "gridcluster")
        self.failUnlessEqual(cluster.threshold, 5)
        self.failUnlessEqual(cluster.threshold_is_percent, True)

    def test_44_verifyshowall(self):
        command = "show cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "High Availability Cluster: utvcs1", command)

    def test_45_verifyplenary_grid_clusterclient(self):
        plenary = os.path.join(self.config.get("broker", "plenarydir"),
                               "cluster", "utgrid1", "client.tpl")
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
                   "--archetype=storagecluster", "--personality=metrocluster"]
        self.noouttest(command)

    def test_51_verifyutstorage1(self):
        command = "show cluster --cluster utstorage1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Storage Cluster: utstorage1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Down Hosts Threshold: 0", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Cluster Personality: metrocluster Archetype: storagecluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_52_verifycatutstorage1(self):
        command = ["cat", "--cluster=utstorage1"]
        out = self.commandtest(command)
        self._verify_cat_on_clusters("utstorage1", "metrocluster", "storage", out, command)

    def test_53_verifyshowutstorage1proto(self):
        command = ["show_cluster", "--cluster=utstorage1", "--format=proto"]
        out = self.commandtest(command)
        clus_list = self.parse_clusters_msg(out, 1)
        cluster = clus_list.clusters[0]
        self.failUnlessEqual(cluster.name, "utstorage1")
        self.failUnlessEqual(cluster.personality.archetype.name,
                             "storagecluster")
        self.failUnlessEqual(cluster.threshold, 0)
        self.failUnlessEqual(cluster.threshold_is_percent, False)

    def test_54_addutstorage2(self):
        command = ["add_cluster", "--cluster=utstorage2",
                   "--building=ut",
                   "--buildstatus=build",
                   "--archetype=storagecluster", "--personality=metrocluster",
                   "--domain=unittest", "--down_hosts_threshold=1",
                   "--max_members=2",
                   "--comments=Another test storage cluster"]
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
        self.matchoutput(out, "Comments: Another test storage cluster", command)

    def test_56_verifycatutstorage2(self):
        command = ["cat", "--cluster=utstorage2"]
        out = self.commandtest(command)
        self._verify_cat_on_clusters("utstorage2", "metrocluster", "storage", out, command)

    def _verify_cat_on_clusters(self, name, persona, type, out, command):
        self.matchoutput(out, "object template clusters/%s;" % name, command)
        self.matchoutput(out, '"/system/cluster/name" = "%s";' % name, command)
        self.matchoutput(out, '"/system/cluster/type" = "%s";' % type, command)
        self.matchoutput(out, '"/system/cluster/sysloc/continent" = "na";', command)
        self.matchoutput(out, '"/system/cluster/sysloc/city" = "ny";', command)
        self.matchoutput(out, '"/system/cluster/sysloc/campus" = "ny";', command)
        self.matchoutput(out, '"/system/cluster/sysloc/building" = "ut";', command)
        self.matchoutput(out, '"/system/cluster/sysloc/location" = "ut.ny.na";', command)
        self.matchoutput(out, '"/system/build" = "build";', command)
        self.matchclean(out, '"/system/cluster/rack/row"', command)
        self.matchclean(out, '"/system/cluster/rack/column"', command)
        self.matchclean(out, '"/system/cluster/rack/name"', command)
        self.matchclean(out, '"/system/cluster/allowed_personalities"', command)
        self.matchclean(out, "include { 'service", command)
        self.matchoutput(out, "include { 'personality/%s/config' };" % persona,
                         command)




if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
