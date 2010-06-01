#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
import sys
import unittest
import re


if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddESXCluster(TestBrokerCommand):

    def testaddutecl1(self):
        command = ["add_esx_cluster", "--cluster=utecl1",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        self.noouttest(command)

    def testverifyutecl1(self):
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.get("broker",
                                      "esx_cluster_max_members_default")
        default_ratio = self.config.get("broker",
                                        "esx_cluster_vm_to_host_ratio")
        self.matchoutput(out, "esx cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Down Hosts Threshold: 2", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: esx_desktop Archetype: vmhost",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def testverifycatutecl1(self):
        command = ["cat", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "object template clusters/utecl1;", command)
        self.matchoutput(out, "'/system/cluster/name' = 'utecl1';", command)
        self.matchoutput(out, "'/system/metacluster/name' = 'utmc1';", command)
        default_ratio = self.config.get("broker",
                                        "esx_cluster_vm_to_host_ratio")
        default_ratio = re.sub(r"(\d+):(\d+)", r"\1, \2", default_ratio)

        self.matchoutput(out, "'/system/cluster/ratio' = list(%s);" % default_ratio, command)
        self.searchoutput(out, r"'/system/cluster/machines' = nlist\(\s*\);",
                          command)
        self.matchclean(out, "include { 'service", command)
        self.matchoutput(out, "include { 'personality/esx_desktop/config' };",
                         command)

    def testaddutecl2(self):
        command = ["add_esx_cluster", "--cluster=utecl2",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=vmhost", "--personality=esx_desktop",
                   "--domain=unittest", "--down_hosts_threshold=1",
                   "--max_members=101", "--vm_to_host_ratio=1:1",
                   "--comments=Another test ESX cluster"]
        self.noouttest(command)

    def testverifyutecl2(self):
        command = "show esx_cluster --cluster utecl2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "esx cluster: utecl2", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 101", command)
        self.matchoutput(out, "vm_to_host_ratio: 1:1", command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Down Hosts Threshold: 1", command)
        self.matchoutput(out, "Personality: esx_desktop Archetype: vmhost",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Comments: Another test ESX cluster", command)

    def testverifycatutecl2(self):
        command = ["cat", "--cluster=utecl2"]
        out = self.commandtest(command)
        self.matchoutput(out, "object template clusters/utecl2;", command)
        self.matchoutput(out, "'/system/cluster/name' = 'utecl2';", command)
        self.matchoutput(out, "'/system/metacluster/name' = 'utmc1';", command)
        self.searchoutput(out, r"'/system/cluster/machines' = nlist\(\s*\);",
                          command)
        self.matchclean(out, "include { 'service", command)

    def testfailaddexisting(self):
        command = ["add_esx_cluster", "--cluster=utecl1",
                   "--metacluster=utmc1", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cluster utecl1 already exists", command)

    def testfailaddnoncampus(self):
        command = ["add_esx_cluster", "--cluster=uteclfail",
                   "--metacluster=utmc1", "--country=us",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Country us is not within a campus", command)

    def testfailmetaclusternotfound(self):
        command = ["add_esx_cluster", "--cluster=utecl999",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=metacluster-does-not-exist", "--building=ut",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found",
                         command)

    def testfailinvalidname(self):
        command = ["add_esx_cluster", "--cluster=invalid?!?",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc1", "--building=ut",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'invalid?!?' is not a valid value for cluster",
                         command)

    def testfailnoroom(self):
        command = ["add_esx_cluster", "--cluster=newcluster",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--metacluster=utmc3", "--building=ut",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "utmc3 already at maximum capacity (0)", command)

    def testverifyshowall(self):
        command = "show esx_cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "esx cluster: utecl1", command)
        self.matchoutput(out, "esx cluster: utecl2", command)

    def testverifyshowmetacluster(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Member: esx cluster utecl1", command)
        self.matchoutput(out, "Member: esx cluster utecl2", command)
        self.matchclean(out, "Member: esx cluster utecl3", command)

    def testnotfoundesx_cluster(self):
        command = "show esx_cluster --cluster esx_cluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def testaddutecl3(self):
        command = ["add_esx_cluster", "--cluster=utecl3",
                   "--max_members=0", "--down_hosts_threshold=2",
                   "--metacluster=utmc2", "--building=ut",
                   "--domain=unittest",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        self.noouttest(command)

    def testverifyutecl3(self):
        command = "show esx_cluster --cluster utecl3"
        out = self.commandtest(command.split(" "))
        default_ratio = self.config.get("broker",
                                        "esx_cluster_vm_to_host_ratio")
        self.matchoutput(out, "esx cluster: utecl3", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 0", command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: esx_desktop Archetype: vmhost",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def testverifycatutecl3(self):
        command = ["cat", "--cluster=utecl3"]
        out = self.commandtest(command)
        self.matchoutput(out, "object template clusters/utecl3;", command)
        self.matchoutput(out, "'/system/cluster/name' = 'utecl3';", command)
        self.matchoutput(out, "'/system/metacluster/name' = 'utmc2';", command)
        self.searchoutput(out, r"'/system/cluster/machines' = nlist\(\s*\);",
                          command)
        self.matchclean(out, "include { 'service", command)

    def testaddutecl4(self):
        # Bog standard - used for some noop tests
        command = ["add_esx_cluster", "--cluster=utecl4",
                   "--metacluster=utmc2", "--building=ut",
                   "--domain=unittest", "--down_hosts_threshold=2",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        self.noouttest(command)

    def testverifyutecl4(self):
        command = "show esx_cluster --cluster utecl4"
        out = self.commandtest(command.split(" "))
        default_ratio = self.config.get("broker",
                                        "esx_cluster_vm_to_host_ratio")
        default_max = self.config.get("broker",
                                      "esx_cluster_max_members_default")
        self.matchoutput(out, "esx cluster: utecl4", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Virtual Machine count: 0", command)
        self.matchoutput(out, "Personality: esx_desktop Archetype: vmhost",
                         command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchclean(out, "Comments", command)

    def testverifycatutecl4(self):
        command = ["cat", "--cluster=utecl4"]
        out = self.commandtest(command)
        self.matchoutput(out, "object template clusters/utecl4;", command)
        self.matchoutput(out, "'/system/cluster/name' = 'utecl4';", command)
        self.matchoutput(out, "'/system/metacluster/name' = 'utmc2';", command)
        self.searchoutput(out, r"'/system/cluster/machines' = nlist\(\s*\);",
                          command)
        self.matchclean(out, "include { 'service", command)

    def testverifyplenaryclusterclient(self):
        for i in range(1, 5):
            cluster = "utecl%s" % i
            plenary = os.path.join(self.config.get("broker", "plenarydir"),
                                   "cluster", cluster, "client.tpl")
            with open(plenary) as f:
                contents = f.read()
            self.matchoutput(contents,
                             "'/system/cluster/name' = '%s';" % cluster,
                             "read %s" % plenary)

    def testaddutmc4(self):
        # Allocate utecl5 - utecl10 for utmc4 (port group testing)
        for i in range(5, 11):
            command = ["add_esx_cluster", "--cluster=utecl%d" % i,
                       "--metacluster=utmc4", "--building=ut",
                       "--domain=unittest", "--down_hosts_threshold=2",
                       "--archetype=vmhost", "--personality=esx_desktop"]
            self.noouttest(command)

    def testfailcatmissingcluster(self):
        command = "cat --cluster=cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Cluster cluster-does-not-exist not found.",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
