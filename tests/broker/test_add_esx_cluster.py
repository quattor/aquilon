#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the add esx_cluster command."""

import os
import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddESXCluster(TestBrokerCommand):

    def testaddutecl1(self):
        # For this cluster, we'll use the default for buildstatus
        # to confirm it does the right thing
        command = ["add_esx_cluster", "--cluster=utecl1",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--maint_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testreconfigureutecl1members(self):
        # Check if reconfiguring an empty list does nothing
        command = ["reconfigure", "--membersof", "utecl1"]
        self.noouttest(command)

    def testverifyutecl1(self):
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.get("archetype_esx_cluster",
                                      "max_members_default")
        default_ratio = self.config.get("archetype_esx_cluster",
                                        "vm_to_host_ratio")
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Maintenance Threshold: 2", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def testverifyutecl1proto(self):
        command = "show esx_cluster --cluster utecl1 --format proto"
        out = self.commandtest(command.split(" "))
        clusterlist = self.parse_clusters_msg(out, expect=1)
        cluster = clusterlist.clusters[0]
        self.failUnlessEqual(cluster.name, "utecl1")
        self.failUnlessEqual(cluster.personality.archetype.name, "esx_cluster")
        self.failUnlessEqual(cluster.threshold, 2)
        self.failUnlessEqual(cluster.threshold_is_percent, False)
        self.failUnlessEqual(cluster.max_members,
                             self.config.getint("archetype_esx_cluster",
                                                "max_members_default"))

    def testverifycatutecl1(self):
        obj_cmd, obj, data_cmd, data = self.verify_cat_clusters("utecl1",
                                                                "vulcan-1g-desktop-prod",
                                                                "esx", "utmc1")

        default_ratio = self.config.get("archetype_esx_cluster",
                                        "vm_to_host_ratio")
        default_ratio = re.sub(r"(\d+):(\d+)", r"\1,\\s*\2", default_ratio)

        self.searchoutput(data, r'"/system/cluster/ratio" = list\(\s*' +
                          default_ratio + r'\s*\);', data_cmd)
        self.matchoutput(data, '"/system/cluster/down_hosts_threshold" = 2;',
                         data_cmd)
        self.matchoutput(data, '"/system/cluster/down_maint_threshold" = 2;',
                         data_cmd)
        self.matchclean(data, '"/system/cluster/down_hosts_as_percent"', data_cmd)
        self.matchclean(data, '"/system/cluster/down_maint_as_percent"', data_cmd)
        self.matchclean(data, '"/system/cluster/down_hosts_percent"', data_cmd)
        self.matchclean(data, '"/system/cluster/down_maint_percent"', data_cmd)

    def testaddutecl2(self):
        command = ["add_esx_cluster", "--cluster=utecl2",
                   "--metacluster=utmc1", "--building=ut",
                   "--buildstatus=build",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod",
                   "--domain=unittest", "--down_hosts_threshold=1",
                   "--max_members=101", "--vm_to_host_ratio=1:1",
                   "--comments=Another test ESX cluster"]
        self.noouttest(command)

    def testverifyutecl2(self):
        command = "show esx_cluster --cluster utecl2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl2", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 101", command)
        self.matchoutput(out, "vm_to_host_ratio: 1:1", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Down Hosts Threshold: 1", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Comments: Another test ESX cluster", command)

    def testverifycatutecl2(self):
        obj_cmd, obj, data_cmd, data = self.verify_cat_clusters("utecl2",
                                                                "vulcan-1g-desktop-prod",
                                                                "esx", "utmc1")

        self.matchoutput(data, '"/system/cluster/down_hosts_threshold" = 1;',
                         data_cmd)

    def testfailaddexisting(self):
        command = ["add_esx_cluster", "--cluster=utecl1",
                   "--metacluster=utmc1", "--building=ut",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cluster utecl1 already exists", command)

    def testfailaddnoncampus(self):
        command = ["add_esx_cluster", "--cluster=uteclfail",
                   "--metacluster=utmc1", "--country=us",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Country us is not within a campus", command)

    def testfailmetaclusternotfound(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--buildstatus=build",
                   "--metacluster=metacluster-does-not-exist", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found",
                         command)

    def testfailbadstatus(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--buildstatus=wanting",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "state wanting not found",
                         command)

    def testfailinvalidname(self):
        command = ["add_esx_cluster", "--cluster=invalid?!?",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--buildstatus=build",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'invalid?!?' is not a valid value for cluster",
                         command)

    def testfailnoroom(self):
        command = ["add_esx_cluster", "--cluster=newcluster",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc3", "--building=ut",
                   "--buildstatus=build",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Metacluster utmc3 already has the maximum "
                         "number of clusters (0).", command)

    def testfaildifferentdomain(self):
        command = ["add_esx_cluster", "--cluster=newcluster",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=ut-prod", "--down_hosts_threshold=2",
                   "--maint_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "ESX Cluster newcluster domain ut-prod does "
                         "not match ESX metacluster utmc1 domain unittest.",
                         command)

    def testverifyshowall(self):
        command = "show esx_cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "ESX Cluster: utecl2", command)

    def testverifyshowmetacluster(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Member: ESX Cluster utecl1", command)
        self.matchoutput(out, "Member: ESX Cluster utecl2", command)
        self.matchclean(out, "Member: ESX Cluster utecl3", command)

    def testnotfoundesx_cluster(self):
        command = "show esx_cluster --cluster esx_cluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def testaddutecl3(self):
        command = ["add_esx_cluster", "--cluster=utecl3",
                   "--max_members=0", "--down_hosts_threshold=2",
                   "--metacluster=utmc2", "--building=ut",
                   "--buildstatus=build",
                   "--domain=unittest",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifyutecl3(self):
        command = "show esx_cluster --cluster utecl3"
        out = self.commandtest(command.split(" "))
        default_ratio = self.config.get("archetype_esx_cluster",
                                        "vm_to_host_ratio")
        self.matchoutput(out, "ESX Cluster: utecl3", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 0", command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def testverifycatutecl3(self):
        self.verify_cat_clusters("utecl3", "vulcan-1g-desktop-prod", "esx", "utmc2")

    def testaddutecl4(self):
        # Bog standard - used for some noop tests
        command = ["add_esx_cluster", "--cluster=utecl4",
                   "--metacluster=utmc2", "--building=ut",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifyutecl4(self):
        command = "show esx_cluster --cluster utecl4"
        out = self.commandtest(command.split(" "))
        default_ratio = self.config.get("archetype_esx_cluster",
                                        "vm_to_host_ratio")
        default_max = self.config.get("archetype_esx_cluster",
                                      "max_members_default")
        self.matchoutput(out, "ESX Cluster: utecl4", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def testverifycatutecl4(self):
        self.verify_cat_clusters("utecl4", "vulcan-1g-desktop-prod", "esx", "utmc2")

    def testverifyplenaryclusterclient(self):
        for i in range(1, 5):
            cluster = "utecl%s" % i
            plenary = os.path.join(self.config.get("broker", "plenarydir"),
                                   "cluster", cluster, "client.tpl")
            with open(plenary) as f:
                contents = f.read()
            self.matchoutput(contents,
                             '"/system/cluster/name" = "%s";' % cluster,
                             "read %s" % plenary)

    def testaddutmc4(self):
        # Allocate utecl5 - utecl10 for utmc4 (port group testing)
        for i in range(5, 11):
            command = ["add_esx_cluster", "--cluster=utecl%d" % i,
                       "--metacluster=utmc4", "--building=ut",
                       "--buildstatus=build",
                       "--domain=unittest", "--down_hosts_threshold=2",
                       "--archetype=esx_cluster",
                       "--personality=vulcan-1g-desktop-prod"]
            self.noouttest(command)

    def testaddutmc5(self):
        command = ["add_esx_cluster", "--cluster=utecl11",
                   "--metacluster=utmc5", "--rack=ut13",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--max_members=15",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)
        command = ["add_esx_cluster", "--cluster=npecl11",
                   "--metacluster=utmc5", "--rack=np13",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--max_members=15",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifyutecl11(self):
        self.verify_cat_clusters("utecl11", "vulcan-1g-desktop-prod", "esx", "utmc5",
                                 on_rack=True)

    def testaddutmc6(self):
        command = ["add_esx_cluster", "--cluster=utecl12",
                   "--metacluster=utmc6", "--rack=ut13",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--max_members=15",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)
        command = ["add_esx_cluster", "--cluster=npecl12",
                   "--metacluster=utmc6", "--rack=np13",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--max_members=15",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifyutecl12(self):
        self.verify_cat_clusters("utecl12", "vulcan-1g-desktop-prod", "esx", "utmc6",
                                 on_rack=True)

    def testaddutmc7(self):
        command = ["add_esx_cluster", "--cluster=utecl13",
                   "--metacluster=utmc7", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testaddsandboxmc(self):
        user = self.config.get("unittest", "user")
        command = ["add_esx_cluster", "--cluster=sandboxcl1",
                   "--metacluster=sandboxmc", "--building=ut",
                   "--sandbox=%s/utsandbox" % user, "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testfailcatmissingcluster(self):
        command = "cat --cluster=cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Cluster cluster-does-not-exist not found.",
                         command)

    def verify_cat_clusters(self, name, persona, ctype, metacluster,
                            on_rack=False):
        object_command = ["cat", "--cluster", name]
        object = self.commandtest(object_command)

        self.matchoutput(object, "object template clusters/%s;" % name,
                         object_command)
        self.searchoutput(object,
                          r'variable LOADPATH = list\(\s*"esx_cluster"\s*\);',
                          object_command)
        self.matchoutput(object, 'include { "clusterdata/%s" };' % name,
                         object_command)
        self.matchclean(object, 'include { "service', object_command)
        self.matchoutput(object, 'include { "personality/%s/config" };' % persona,
                         object_command)

        data_command = ["cat", "--cluster", name, "--data"]
        data = self.commandtest(data_command)

        self.matchoutput(data, "template clusterdata/%s;" % name, data_command)
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
        self.matchoutput(data, '"/system/metacluster/name" = "%s";' %
                         metacluster, data_command)
        self.matchoutput(data, '"/system/build" = "build";', data_command)
        if on_rack:
            self.matchoutput(data, '"/system/cluster/rack/name" = "ut13"',
                             data_command)
            self.matchoutput(data, '"/system/cluster/rack/row" = "k"',
                             data_command)
            self.matchoutput(data, '"/system/cluster/rack/column" = "3"',
                             data_command)
        else:
            self.matchclean(data, '"/system/cluster/rack/name"', data_command)
            self.matchclean(data, '"/system/cluster/rack/row"', data_command)
            self.matchclean(data, '"/system/cluster/rack/column"', data_command)
        self.matchclean(data, '"/system/cluster/allowed_personalities"', data_command)
        self.matchclean(data, "resources/virtual_machine", data_command)

        return object_command, object, data_command, data


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
