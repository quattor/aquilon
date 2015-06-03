#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the add esx_cluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestAddESXCluster(PersonalityTestMixin, TestBrokerCommand):

    def test_100_add_personality(self):
        vmhost_maps = {
            "esx_management_server": {
                "ut.a": {
                    "building": ["ut"],
                },
                "ut.b": {
                    "building": ["ut"],
                },
            },
            "vmseasoning": {
                "salt": {
                    "building": ["ut"],
                },
                "pepper": {
                    "building": ["ut"],
                },
            },
        }
        esx_cluster_maps = {
            "esx_management_server": {
                "ut.a": {
                    "building": ["ut"],
                },
                "ut.b": {
                    "building": ["ut"],
                },
            },
        }

        self.create_personality("vmhost", "vulcan-10g-server-prod",
                                grn="grn:/ms/ei/aquilon/aqd",
                                environment="prod",
                                required=["esx_management_server",
                                          "vmseasoning"],
                                maps=vmhost_maps)
        self.create_personality("esx_cluster", "vulcan-10g-server-prod",
                                grn="grn:/ms/ei/aquilon/aqd",
                                environment="prod",
                                maps=esx_cluster_maps)
        self.create_personality("esx_cluster", "nostage", staged=True)

    def test_110_add_utecl1(self):
        # For this cluster, we'll use the default for buildstatus
        # to confirm it does the right thing
        command = ["add_esx_cluster", "--cluster=utecl1",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--maint_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)

    def test_111_reconfigure_utecl1_members(self):
        # Check if reconfiguring an empty list does nothing
        command = ["reconfigure", "--membersof", "utecl1"]
        self.noouttest(command)

    def test_115_show_utecl1(self):
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.getint("archetype_esx_cluster",
                                         "max_members_default")
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Maintenance Threshold: 2", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Personality: vulcan-10g-server-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_115_show_utecl1_proto(self):
        command = "show esx_cluster --cluster utecl1 --format proto"
        cluster = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(cluster.name, "utecl1")
        self.assertEqual(cluster.metacluster, "utmc1")
        self.assertEqual(cluster.location_constraint.name, "ut")
        self.assertEqual(cluster.location_constraint.location_type, "building")
        self.assertEqual(cluster.personality.archetype.name, "esx_cluster")
        self.assertEqual(cluster.personality.name, "vulcan-10g-server-prod")
        self.assertEqual(cluster.domain.name, "unittest")
        self.assertEqual(cluster.domain.type, cluster.domain.DOMAIN)
        self.assertEqual(cluster.threshold, 2)
        self.assertEqual(cluster.threshold_is_percent, False)
        self.assertEqual(cluster.max_members,
                         self.config.getint("archetype_esx_cluster",
                                            "max_members_default"))

    def test_120_add_utecl2(self):
        command = ["add_esx_cluster", "--cluster=utecl2",
                   "--metacluster=utmc1", "--building=ut",
                   "--buildstatus=build",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod",
                   "--domain=unittest", "--down_hosts_threshold=1",
                   "--max_members=101", "--vm_to_host_ratio=1:1",
                   "--comments=Some ESX cluster comments"]
        err = self.statustest(command)
        self.matchoutput(err, "The --vm_to_host_ratio option is deprecated.",
                         command)

    def test_125_show_utecl2(self):
        command = "show esx_cluster --cluster utecl2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl2", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 101", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Down Hosts Threshold: 1", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Personality: vulcan-10g-server-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Comments: Some ESX cluster comments", command)

    def test_130_add_utecl3(self):
        command = ["add_esx_cluster", "--cluster=utecl3",
                   "--max_members=0", "--down_hosts_threshold=2",
                   "--metacluster=utmc2", "--building=ut",
                   "--domain=unittest",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)

    def test_135_show_utecl3(self):
        command = "show esx_cluster --cluster utecl3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl3", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 0", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: vulcan-10g-server-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_140_add_utecl4(self):
        # Bog standard - used for some noop tests
        command = ["add_esx_cluster", "--cluster=utecl4",
                   "--metacluster=utmc2", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)

    def test_145_show_utecl4(self):
        command = "show esx_cluster --cluster utecl4"
        out = self.commandtest(command.split(" "))
        default_max = self.config.getint("archetype_esx_cluster",
                                         "max_members_default")
        self.matchoutput(out, "ESX Cluster: utecl4", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: vulcan-10g-server-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def test_148_verify_cluster_client(self):
        for i in range(1, 5):
            cluster = "utecl%s" % i
            plenary = self.plenary_name("cluster", cluster, "client")
            with open(plenary) as f:
                contents = f.read()
            self.matchoutput(contents,
                             '"/system/cluster/name" = "%s";' % cluster,
                             "read %s" % plenary)

    def test_150_add_utmc4(self):
        # Allocate utecl5 - utecl10 for utmc4 (port group testing)
        for i in range(5, 11):
            command = ["add_esx_cluster", "--cluster=utecl%d" % i,
                       "--metacluster=utmc4", "--building=ut",
                       "--domain=unittest", "--down_hosts_threshold=2",
                       "--archetype=esx_cluster",
                       "--personality=vulcan-10g-server-prod"]
            self.noouttest(command)

    def test_160_add_utmc7(self):
        command = ["add_esx_cluster", "--cluster=utecl13",
                   "--metacluster=utmc7", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)

    def test_170_add_sandboxmc(self):
        command = ["add_esx_cluster", "--cluster=sandboxcl1",
                   "--metacluster=sandboxmc", "--building=ut",
                   "--sandbox=%s/utsandbox" % self.user, "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)

    def test_200_cat_missing_cluster(self):
        command = "cat --cluster=cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Cluster cluster-does-not-exist not found.",
                         command)

    def test_200_add_duplicate(self):
        command = ["add_esx_cluster", "--cluster=utecl1",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cluster utecl1 already exists", command)

    def test_200_add_bad_metacluster(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=metacluster-does-not-exist", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found",
                         command)

    def test_200_add_bad_status(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--buildstatus=wanting",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown cluster lifecycle 'wanting'",
                         command)

    def test_200_add_bad_name(self):
        command = ["add_esx_cluster", "--cluster=invalid?!?",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'invalid?!?' is not a valid value for cluster",
                         command)

    def test_200_metacluster_capacity(self):
        command = ["add_esx_cluster", "--cluster=newcluster",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc3", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Metacluster utmc3 has 1 clusters bound, which "
                         "exceeds the requested limit of 0.", command)

    def test_200_domain_mismatch(self):
        command = ["add_esx_cluster", "--cluster=newcluster",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=ut-prod", "--down_hosts_threshold=2",
                   "--maint_threshold=2",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-10g-server-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "ESX Cluster newcluster domain ut-prod does "
                         "not match ESX metacluster utmc1 domain unittest.",
                         command)

    def test_200_missing_personality(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster",
                   "--personality=personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality personality-does-not-exist, "
                         "archetype esx_cluster not found",
                         command)

    def test_200_missing_personality_stage(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster", "--personality=nostage",
                   "--personality_stage=previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality esx_cluster/nostage "
                         "does not have stage previous.",
                         command)

    def test_200_bad_personality_stage(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=esx_cluster", "--personality=nostage",
                   "--personality_stage=no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'no-such-stage' is not a valid personality stage.",
                         command)

    def test_200_show_missing(self):
        command = "show esx_cluster --cluster esx_cluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_300_search_esx(self):
        command = "search cluster --cluster_type esx"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)

    def test_300_show_metacluster(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Member: ESX Cluster utecl1", command)
        self.matchoutput(out, "Member: ESX Cluster utecl2", command)
        self.matchclean(out, "Member: ESX Cluster utecl3", command)

    def test_300_show_metacluster_proto(self):
        command = "show metacluster --metacluster utmc1 --format proto"
        mc = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(mc.name, "utmc1")
        self.assertEqual(len(mc.clusters), 2)
        self.assertEqual(set(cluster.name for cluster in mc.clusters),
                         set(["utecl1", "utecl2"]))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
