#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the cluster command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestCluster(TestBrokerCommand):

    def testbindutecl1(self):
        for i in range(1, 5):
            self.successtest(["cluster",
                              "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                              "--personality=esx_desktop",
                              "--cluster", "utecl1"])

    def testbindutecl2(self):
        # test_rebind_esx_cluster will also bind evh1 to utecl2.
        for i in [5]:
            self.successtest(["cluster",
                              "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                              "--personality=esx_desktop",
                              "--cluster", "utecl2"])

    def testduplicatebindutecl1(self):
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--personality=esx_desktop",
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
            self.matchoutput(out, "Member: evh%s.aqd-unittest.ms.com" %i,
                             command)

    def testverifycat(self):
        cat_cluster_command = "cat --cluster utecl1"
        cat_cluster_out = self.commandtest(cat_cluster_command.split())
        m = self.searchoutput(cat_cluster_out,
                              r"include { '(service/esx_management_server/"
                              r"ut.[ab]/client/config)' };",
                              cat_cluster_command)
        template = m.group(1)
        for i in range(1, 5):
            host = "evh%s.aqd-unittest.ms.com" % i
            self.searchoutput(cat_cluster_out,
                              '"/system/cluster/members" = list\([^\)]*'
                              '"%s"[^\)]*\);' % host,
                              cat_cluster_command)

            # Also verify that the host plenary was written correctly.
            cat_host_command = ["cat", "--hostname", host]
            cat_host_out = self.commandtest(cat_host_command)
            self.matchoutput(cat_host_out,
                             """include { "%s" };""" % template,
                             cat_host_command)

        for i in range(1, 5):
            command = "cat --hostname evh%s.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split())
            self.searchoutput(out,
                              "'/system/cluster/name' = \"utecl1\";",
                              command)
            self.searchoutput(out,
                              "include { \"cluster/utecl1/client\" };",
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
                   "--personality=esx_desktop"]
        # Currently aquilon61 will be an "aquilon" archetype. Which is
        # incompatible with esx_desktop...
        out = self.notfoundtest(command)

        # So, make it a compatible archetype and try again
        command = ["reconfigure", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=esx_server", "--archetype=vmhost",
                   "--os=esxi/4.0.0", "--buildstatus=rebuild"]
        self.successtest(command)
        command = ["cluster", "--cluster=utecl1",
                   "--personality=esx_desktop",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        user = self.config.get("unittest", "user")
        self.matchoutput(out,
                         "Host aquilon61.aqd-unittest.ms.com sandbox "
                         "%s/utsandbox does not match ESX cluster utecl1 "
                         "domain unittest" % user,
                         command)

        # Ah yes, we need it to be in the same sandbox
        command = ["manage", "--domain=unittest",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["cluster", "--cluster=utecl1",
                   "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=esx_desktop"]
        self.successtest(command)

        # Restore the host.  Need to move to a more permissive cluster first.
        command = ["cluster", "--cluster=utecl2",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        self.successtest(command)

        # Now try to uncluster it...
        command = ["uncluster", "--cluster=utecl2",
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host personality esx_desktop requires a cluster, "
                         "use --personality to change personality when "
                         "leaving the cluster.",
                         command)

        # Oops.
        command = ["uncluster", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--cluster=utecl2", "--personality=generic"]
        out = self.successtest(command)

        user = self.config.get("unittest", "user")
        command = ["manage", "--sandbox=%s/utsandbox" % user,
                   "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["reconfigure", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--personality=inventory", "--archetype=aquilon",
                   "--os=linux/5.0.1-x86_64", "--buildstatus=rebuild"]
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
