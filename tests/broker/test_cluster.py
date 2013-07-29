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
"""Module for testing the cluster command."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestCluster(TestBrokerCommand):

    def testbindutecl1(self):
        for i in range(1, 5):
            self.successtest(["cluster",
                              "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                              "--personality=vulcan-1g-desktop-prod",
                              "--cluster", "utecl1"])

    def testbindutecl2(self):
        # test_rebind_esx_cluster will also bind evh1 to utecl2.
        for i in [5]:
            self.successtest(["cluster",
                              "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                              "--personality=vulcan-1g-desktop-prod",
                              "--cluster", "utecl2"])

    def testduplicatebindutecl1(self):
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--personality=vulcan-1g-desktop-prod",
                          "--cluster", "utecl1"])

    def testverifybindutecl1(self):
        for i in range(1, 5):
            command = "show host --hostname evh%s.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Primary Name: evh%s.aqd-unittest.ms.com" % i,
                             command)
            self.matchoutput(out, "Member of ESX Cluster: utecl1", command)
        command = "show esx cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        for i in range(1, 5):
            self.matchoutput(out, "Member: evh%d.aqd-unittest.ms.com "
                             "[node_index: %d]" % (i, i - 1), command)

    def testverifycat(self):
        cat_cluster_command = "cat --cluster utecl1"
        cat_cluster_out = self.commandtest(cat_cluster_command.split())
        m = self.searchoutput(cat_cluster_out,
                              r'include { "(service/esx_management_server/ut.[ab]/client/config)" };',
                              cat_cluster_command)
        template = m.group(1)
        cat_cluster_command = "cat --cluster utecl1 --data"
        cat_cluster_out = self.commandtest(cat_cluster_command.split())
        for i in range(1, 5):
            host = "evh%s.aqd-unittest.ms.com" % i
            self.searchoutput(cat_cluster_out,
                              '"system/cluster/members" = list\([^\)]*'
                              '"%s"[^\)]*\);' % host,
                              cat_cluster_command)

            # Also verify that the host plenary was written correctly.
            cat_host_command = ["cat", "--hostname", host]
            cat_host_out = self.commandtest(cat_host_command)
            self.matchoutput(cat_host_out,
                             'include { "%s" };' % template,
                             cat_host_command)

        for i in range(1, 5):
            command = "cat --hostname evh%s.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split())
            self.searchoutput(out,
                              'include { "cluster/utecl1/client" };',
                              command)
            command = "cat --hostname evh%s.aqd-unittest.ms.com --data" % i
            out = self.commandtest(command.split())
            self.searchoutput(out,
                              '"system/cluster/name" = "utecl1";',
                              command)

    def testfailmissingcluster(self):
        command = ["cluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def test_switching_archetype(self):
        command = ["cluster", "--cluster=utecl1",
                   "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=vulcan-1g-desktop-prod"]
        # Currently aquilon61 will be an "aquilon" archetype. Which is
        # incompatible with vulcan-1g-desktop-prod...
        out = self.notfoundtest(command)

        # So, make it a compatible archetype and try again
        command = ["reconfigure", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=esx_server", "--archetype=vmhost",
                   "--osname", "esxi", "--osversion", "4.0.0",
                   "--buildstatus=rebuild"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "Warning: Host aquilon61.aqd-unittest.ms.com "
                         "personality esx_server requires cluster membership, "
                         "please run 'aq cluster'.",
                         command)
        command = ["cluster", "--cluster=utecl1",
                   "--personality=vulcan-1g-desktop-prod",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        user = self.config.get("unittest", "user")
        self.matchoutput(out,
                         "Host aquilon61.aqd-unittest.ms.com sandbox "
                         "%s/utsandbox does not match ESX cluster utecl1 "
                         "domain unittest" % user,
                         command)

        # Ah yes, we need it to be in the same sandbox
        # using --force to bypass normal checks due to git status
        # containing uncommitted files
        command = ["manage", "--domain=unittest",
                   "--hostname=aquilon61.aqd-unittest.ms.com", "--force"]
        self.successtest(command)

        command = ["cluster", "--cluster=utecl1",
                   "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=vulcan-1g-desktop-prod"]
        self.successtest(command)

        # Restore the host.  Need to move to a more permissive cluster first.
        command = ["cluster", "--cluster=utecl2",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        self.successtest(command)

        # Check that both cluster plenaries were updated
        command = ["cat", "--cluster", "utecl1"]
        out = self.commandtest(command)
        self.matchclean(out, "aquilon61.aqd-unittest.ms.com", command)
        command = ["cat", "--cluster", "utecl2", "--data"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"system/cluster/members" = list\('
                          r'[^)]*"aquilon61.aqd-unittest.ms.com"[^)]*\);',
                          command)

        # Now try to uncluster it...
        command = ["uncluster", "--cluster=utecl2",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host personality vulcan-1g-desktop-prod requires a cluster, "
                         "use --personality to change personality when "
                         "leaving the cluster.",
                         command)

        # Oops.
        command = ["uncluster", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--cluster=utecl2", "--personality=generic"]
        out = self.successtest(command)

        user = self.config.get("unittest", "user")
        # using --force to bypass normal checks due to git status
        # containing uncommitted files
        command = ["manage", "--sandbox=%s/utsandbox" % user,
                   "--hostname=aquilon61.aqd-unittest.ms.com", "--force"]
        out = self.commandtest(command)

        command = ["reconfigure", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=inventory", "--archetype=aquilon",
                   "--osname=linux", "--osversion=5.0.1-x86_64",
                   "--buildstatus=rebuild"]
        self.successtest(command)

    def testfailbadlocation(self):
        command = ["cluster", "--hostname=%s.ms.com" % self.aurora_with_node,
                   "--cluster", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is not within cluster location", command)

    def testfailmaxmembers(self):
        command = ["cluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "utecl3"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl3 is over capacity of 0 hosts.",
                         command)

    def testfailunmadecluster(self):
        command = ["cluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "utecl4"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Please run `make cluster --cluster utecl4`",
                         command)

    def testbindutmc4(self):
        for i in range(1, 25):
            host = "evh%s.aqd-unittest.ms.com" % (i + 50)
            cluster = "utecl%d" % (5 + ((i - 1) / 4))
            self.successtest(["cluster",
                              "--hostname", host, "--cluster", cluster])

    def testbindstoragecluster(self):
        command = ["cluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster=utstorage1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "only hosts with archetype 'filer' can be added",
                         command)

        command = ["cluster", "--hostname=filer1.ms.com",
                   "--cluster=utstorage1"]
        self.successtest(command)

    def testbindhaclusters(self):
        for i in range(25, 49):
            host = "evh%s.aqd-unittest.ms.com" % (i + 50)
            cluster = "utecl%d" % (11 + ((i - 25) / 12))
            self.successtest(["cluster",
                              "--hostname", host, "--cluster", cluster])
            host = "evh%s.one-nyp.ms.com" % (i + 50)
            cluster = "npecl%d" % (11 + ((i - 25) / 12))
            self.successtest(["cluster",
                              "--hostname", host, "--cluster", cluster])

            command = ["show_cluster", "--cluster", cluster, "--format=proto"]
            out = self.commandtest(command)
            clus_list = self.parse_clusters_msg(out, 1)
            clustobj = clus_list.clusters[0]
            hostfromproto = filter(lambda x: x.fqdn == host, clustobj.hosts)
            self.assertEqual(len(hostfromproto), 1)

    def testclusterutmc7(self):
        host = "evh10.aqd-unittest.ms.com"
        cluster = "utecl13"
        self.successtest(["cluster", "--hostname", host, "--cluster", cluster])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
