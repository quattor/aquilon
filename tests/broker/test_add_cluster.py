#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
        default_max = self.config.get("archetype_hacluster",
                                      "max_members_default")
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
        obj_cmd, obj, data_cmd, data = self.verify_cat_clusters("utvcs1",
                                                                "hacluster",
                                                                "vcs-msvcs",
                                                                "compute")

        self.matchoutput(data, '"/system/cluster/down_hosts_threshold" = 0;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_maint_threshold" = 1;',
                         data_cmd)
        self.matchclean(data, '"/system/cluster/down_hosts_as_percent"',
                        data_cmd)
        self.matchclean(data, '"/system/cluster/down_maint_as_percent"',
                        data_cmd)
        self.matchclean(data, '"/system/cluster/down_hosts_percent"', data_cmd)
        self.matchclean(data, '"/system/cluster/down_maint_percent"', data_cmd)

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

    def test_20_fail_nomanage(self):
        command = ["add_cluster", "--cluster=utvcs2",
                   "--building=ut",
                   "--domain=nomanage", "--down_hosts_threshold=0",
                   "--maint_threshold=1",
                   "--archetype=hacluster", "--personality=vcs-msvcs"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Adding clusters to domain nomanage "
                         "is not allowed.", command)

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
                   "--maint_threshold=6%",
                   "--archetype=gridcluster", "--personality=hadoop"]
        self.noouttest(command)

    def get_grid_max(self):
        return self.config.getint("archetype_gridcluster", "max_members_default")

    def test_41_verify_utgrid1(self):
        command = "show cluster --cluster utgrid1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Grid Cluster: utgrid1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Down Hosts Threshold: 0 (5%)", command)
        self.matchoutput(out, "Maintenance Threshold: 0 (6%)", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Cluster Personality: hadoop Archetype: gridcluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)
        self.matchoutput(out, "Max members: %d" % self.get_grid_max(), command)

    def test_42_verifycatutgrid1(self):
        obj_cmd, obj, data_cmd, data = self.verify_cat_clusters("utgrid1",
                                                                "gridcluster",
                                                                "hadoop",
                                                                "compute")

        self.matchoutput(data, '"/system/cluster/down_hosts_threshold" = 0;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_maint_threshold" = 0;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_hosts_as_percent" = true;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_maint_as_percent" = true;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_hosts_percent" = 5;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_maint_percent" = 6;',
                         data_cmd)

    def test_43_verifyshowutgrid1proto(self):
        command = ["show_cluster", "--cluster=utgrid1", "--format=proto"]
        out = self.commandtest(command)
        clus_list = self.parse_clusters_msg(out, 1)
        cluster = clus_list.clusters[0]
        self.failUnlessEqual(cluster.name, "utgrid1")
        self.failUnlessEqual(cluster.personality.archetype.name, "gridcluster")
        self.failUnlessEqual(cluster.threshold, 5)
        self.failUnlessEqual(cluster.threshold_is_percent, True)
        self.failUnlessEqual(cluster.max_members, self.get_grid_max())

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
        # This archetype is non-compilable and should not have a plenary!
        #self.verify_cat_clusters("utstorage1", "storagecluster",
        #                         "metrocluster", "storage")
        command = ["cat", "--cluster", "utstorage1"]
        err = self.internalerrortest(command)
        self.matchoutput(err, "No such file or directory", command)

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
        # This archetype is non-compilable and should not have a plenary!
        #self.verify_cat_clusters("utstorage2", "storagecluster",
        #                         "metrocluster", "storage")
        command = ["cat", "--cluster", "utstorage2"]
        err = self.internalerrortest(command)
        self.matchoutput(err, "No such file or directory", command)

    def verify_cat_clusters(self, name, archetype, persona, ctype):
        """ generic method to verify common attributes for cat on clusters """
        object_command = ["cat", "--cluster", name]
        object = self.commandtest(object_command)

        self.matchoutput(object, "object template clusters/%s;" % name,
                         object_command)
        self.searchoutput(object,
                          r'variable LOADPATH = list\(\s*"%s"\s*\);' % archetype,
                          object_command)
        self.matchoutput(object, 'include { "clusterdata/%s" };' % name,
                         object_command)
        self.matchclean(object, 'include { "service', object_command)
        self.matchoutput(object, 'include { "personality/%s/config" };' % persona,
                         object_command)

        self.matchoutput(object,
                         '"/metadata/template/branch/name" = "unittest";',
                         object_command)
        self.matchoutput(object,
                         '"/metadata/template/branch/type" = "domain";',
                         object_command)
        self.matchclean(object,
                        '"/metadata/template/branch/author"',
                        object_command)

        data_command = ["cat", "--cluster", name, "--data"]
        data = self.commandtest(data_command)

        self.matchoutput(data, "template clusterdata/%s" % name,
                         data_command)
        self.matchoutput(data, '"/system/cluster/name" = "%s";' % name,
                         data_command)
        self.matchoutput(data, '"/system/cluster/type" = "%s";' % ctype,
                         data_command)
        self.matchoutput(data, '"/system/cluster/sysloc/continent" = "na";',
                         data_command)
        self.matchoutput(data, '"/system/cluster/sysloc/city" = "ny";',
                         data_command)
        self.matchoutput(data, '"/system/cluster/sysloc/campus" = "ny";',
                         data_command)
        self.matchoutput(data, '"/system/cluster/sysloc/building" = "ut";',
                         data_command)
        self.matchoutput(data, '"/system/cluster/sysloc/location" = "ut.ny.na";',
                         data_command)
        self.matchoutput(data, '"/system/build" = "build";', data_command)
        self.matchclean(data, '"/system/cluster/rack/row"', data_command)
        self.matchclean(data, '"/system/cluster/rack/column"', data_command)
        self.matchclean(data, '"/system/cluster/rack/name"', data_command)
        self.matchclean(data, '"/system/cluster/allowed_personalities"', data_command)

        return object_command, object, data_command, data

    def test_57_addutstorages2(self):
        user = self.config.get("unittest", "user")
        command = ["add_cluster", "--cluster=utstorages2",
                   "--building=bu",
                   "--buildstatus=ready",
                   "--archetype=storagecluster", "--personality=metrocluster",
                   "--sandbox=%s/utsandbox" % user, "--down_hosts_threshold=1",
                   "--max_members=2",
                   "--comments=Test storage cluster for sandbox"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
