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
"""Module for testing the update esx_cluster command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestUpdateESXCluster(TestBrokerCommand):

    def testupdatenoop(self):
        default_max = self.config.get("broker",
                                      "esx_cluster_max_members_default")
        self.noouttest(["update_esx_cluster", "--cluster=utecl4",
                        "--building=ut"])

    def testverifynoop(self):
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
        self.matchoutput(out, "Personality: esx_server Archetype: vmhost",
                         command)
        self.matchclean(out, "Comments", command)

    def testupdateutecl2(self):
        command = ["update_esx_cluster", "--cluster=utecl2",
                   "--max_members=97", "--vm_to_host_ratio=5:1",
                   "--comments", "ESX Cluster with a new comment",
                   "--down_hosts_threshold=0"]
        self.noouttest(command)

    def testverifyutecl2(self):
        command = "show esx_cluster --cluster utecl2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "esx cluster: utecl2", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 97", command)
        self.matchoutput(out, "vm_to_host_ratio: 5:1", command)
        self.matchoutput(out, "Down Hosts Threshold: 0",command)
        self.matchoutput(out, "Personality: esx_server Archetype: vmhost",
                         command)
        self.matchoutput(out, "Comments: ESX Cluster with a new comment",
                         command)

    def testupdateutecl3(self):
        # Testing both that an empty cluster can have its personality
        # updated and that personality without archetype will assume
        # the current archetype.
        command = ["update_esx_cluster", "--cluster=utecl3",
                   "--personality=esx_desktop"]
        self.noouttest(command)

    def testverifyutecl3(self):
        command = "show esx_cluster --cluster utecl3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "esx cluster: utecl3", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Personality: esx_desktop Archetype: vmhost",
                         command)

    def testupdateutecl1(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--rack=ut10"]
        self.noouttest(command)

    def testupdateutecl1switch(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--tor_switch=ut01ga1s04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testupdateutecl1switchfail(self):
        # Try something that is not a tor_switch
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--tor_switch=unittest02.one-nyp.ms.com"]
        self.badrequesttest(command)

    def testfailupdatelocation(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--rack=ut3"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot set esx cluster utecl1 location constraint "
                         "to Rack ut3: Host",
                         command)

    def testfailupdatenoncampus(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--country=us"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "location country 'us' is not within a campus",
                         command)

    def testfailupdatepersonality(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--archetype=vmhost", "--personality=esx_desktop"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot change cluster personality while containing "
                         "members of a different personality:",
                         command)

    def testfailupdatearchetype(self):
        # If personality is not specified the current personality name
        # is assumed for the new archetype.
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--archetype=windows"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality esx_server in Archetype windows "
                         "not found",
                         command)

    def testfailupdatemaxmembers(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--max_members=0"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "value already exceeded", command)

    def testfailupdateratio(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--vm_to_host_ratio=0"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "violates ratio", command)

    def testfailupdaterealratio(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--vm_to_host_ratio=2:1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "violates ratio", command)

    def testfailupdatedht(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--down_hosts_threshold=4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot support VMs", command)

    def testverifyutecl1(self):
        default_max = self.config.get("broker",
                                      "esx_cluster_max_members_default")
        default_ratio = self.config.get("broker",
                                        "esx_cluster_vm_to_host_ratio")
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "esx cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Rack: ut10", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Personality: esx_server Archetype: vmhost",
                         command)
        self.matchoutput(out, "ToR Switch: ut01ga1s04.aqd-unittest.ms.com",
                         command)

    def testfailmissingcluster(self):
        command = ["update_esx_cluster", "--cluster=cluster-does-not-exist",
                   "--comments=test should fail"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "cluster 'cluster-does-not-exist' not found",
                         command)

    # FIXME: Need tests for plenary templates
    # FIXME: Include test that machine plenary moved correctly


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
