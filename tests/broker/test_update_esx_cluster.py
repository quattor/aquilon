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
"""Module for testing the update esx_cluster command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateESXCluster(TestBrokerCommand):

    def test_100_updatenoop(self):
        default_max = self.config.get("archetype_esx_cluster",
                                      "max_members_default")
        self.noouttest(["update_esx_cluster", "--cluster=utecl4",
                        "--building=ut"])

    def test_110_verifynoop(self):
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
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchclean(out, "Comments", command)

    def test_200_updateutecl2(self):
        command = ["update_esx_cluster", "--cluster=utecl2",
                   "--max_members=97", "--vm_to_host_ratio=5:1",
                   "--comments", "ESX Cluster with a new comment",
                   "--memory_capacity", 16384,
                   "--down_hosts_threshold=0"]
        self.noouttest(command)

    def test_210_verifyutecl2(self):
        command = "show esx_cluster --cluster utecl2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl2", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Max members: 97", command)
        self.matchoutput(out, "vm_to_host_ratio: 5:1", command)
        self.matchoutput(out, "Down Hosts Threshold: 0", command)
        self.matchoutput(out, "Capacity limits: memory: 16384 [override]",
                         command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Comments: ESX Cluster with a new comment",
                         command)

    def test_220_verifysearchoverride(self):
        command = ["search_esx_cluster", "--capacity_override"]
        out = self.commandtest(command)
        self.matchclean(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)
        self.matchclean(out, "utecl5", command)

    def test_225_verifynooverrideflag(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchclean(out, "override", command)

    def test_230_failupdateutecl2(self):
        command = ["update_esx_cluster", "--cluster", "utecl2",
                   "--memory_capacity", 1024]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl2 is over capacity regarding memory",
                         command)

    def test_240_clearoverrideutecl2(self):
        command = ["update_esx_cluster", "--cluster", "utecl2",
                   "--clear_overrides"]
        self.noouttest(command)

    def test_250_verifyclearoverride(self):
        command = ["show_esx_cluster", "--cluster", "utecl2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Capacity limits: memory: 157236", command)

    def test_260_verifyclearsearchoverride(self):
        command = ["search_esx_cluster", "--capacity_override"]
        out = self.commandtest(command)
        self.matchclean(out, "utecl2", command)

    def test_300_updateutecl3(self):
        # Testing both that an empty cluster can have its personality
        # updated and that personality without archetype will assume
        # the current archetype.
        command = ["update_esx_cluster", "--cluster=utecl3",
                   "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def test_310_verifyutecl3(self):
        command = "show esx_cluster --cluster utecl3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl3", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)

    def test_320_updateutecl1(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--rack=ut10"]
        self.noouttest(command)

    def test_330_updateutecl1switch(self):
        # Deprecated.
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--switch=ut01ga1s04.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_340_updateutecl1switchfail(self):
        # Try something that is not a tor_switch
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--switch=unittest02.one-nyp.ms.com"]
        self.badrequesttest(command)

    def test_350_failupdatelocation(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--rack=ut3"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot set ESX Cluster utecl1 location constraint "
                         "to Rack ut3:",
                         command)

    def test_360_failupdatenoncampus(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--country=us"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Country us is not within a campus",
                         command)

    def test_370_updatepersonality(self):
        command = ["search_host", "--cluster=utecl1",
                   "--personality=vulcan-1g-desktop-prod"]
        original_hosts = self.commandtest(command).splitlines()
        original_hosts.sort()
        self.failUnless(original_hosts, "No hosts found using %s" % command)

        # Also test that the host plenary will be re-written correctly.
        command = ["cat", "--hostname", original_hosts[0]]
        out = self.commandtest(command)
        self.matchoutput(out,
            """include { "personality/vulcan-1g-desktop-prod/config" };""",
            command)

        command = ["reconfigure", "--membersof=utecl1",
                   "--archetype=vmhost",
                   "--osname=esxi", "--osver=4.1.0-u1"]
        out = self.successtest(command)

        command = ["search_host", "--cluster=utecl1",
                   "--osversion=4.1.0-u1"]
        updated_hosts = self.commandtest(command).splitlines()
        updated_hosts.sort()
        self.failUnless(updated_hosts, "No hosts found using %s" % command)

        self.failUnlessEqual(original_hosts, updated_hosts,
                             "Expected only/all updated hosts %s to match the "
                             "list of original hosts %s" %
                             (updated_hosts, original_hosts))

        command = ["cat", "--hostname", updated_hosts[0]]
        out = self.commandtest(command)
        self.matchoutput(out,
            """include { "os/esxi/4.1.0-u1/config" };""",
            command)

        command = ["reconfigure", "--membersof=utecl1",
                   "--archetype=vmhost", "--osname=esxi",
                   "--osversion=4.0.0"]
        out = self.successtest(command)

    def test_380_failupdatearchetype(self):
        # If personality is not specified the current personality name
        # is assumed for the new archetype.
        command = ["reconfigure", "--membersof=utecl1",
                   "--archetype=windows"]
        out = self.badrequesttest(command)
        # The command complains both about the broker personality and OS.
        self.matchoutput(out,
                         "No personality vulcan-1g-desktop-prod found for "
                         "archetype windows.",
                         command)
        self.matchoutput(out,
                         "Cannot change archetype because operating system "
                         "vmhost/esxi-4.0.0 needs archetype vmhost.",
                         command)

    def test_390_failupdatemaxmembers(self):
        command = ["update_esx_cluster", "--cluster=utecl1", "--max_members=0"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl1 has 3 hosts bound, which exceeds "
                         "the requested limit 0.",
                         command)

    def test_400_failupdateratio(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--vm_to_host_ratio=0"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "violates ratio", command)

    def test_400_failupdateillegalratio(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--vm_to_host_ratio=not-a:number"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Expected a ratio like", command)

    def test_410_failupdaterealratio(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--vm_to_host_ratio=2:1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "violates ratio", command)

    def test_420_failupdatedht(self):
        command = ["update_esx_cluster", "--cluster=utecl1",
                   "--down_hosts_threshold=4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot support VMs", command)

    def test_450_verifyutecl1(self):
        default_max = self.config.get("archetype_esx_cluster",
                                      "max_members_default")
        default_ratio = self.config.get("archetype_esx_cluster",
                                        "vm_to_host_ratio")
        command = "show esx_cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Rack: ut10", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchoutput(out, "vm_to_host_ratio: %s" % default_ratio, command)
        self.matchoutput(out, "Personality: vulcan-1g-desktop-prod Archetype: esx_cluster",
                         command)
        self.matchoutput(out, "Switch: ut01ga1s04.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Capacity limits: memory: 78618", command)
        self.matchoutput(out, "Resources used by VMs: memory: 32768", command)

    def test_460_searchswitch(self):
        command = ["search", "esx", "cluster", "--switch",
                   "ut01ga1s04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl1", command)
        self.matchclean(out, "utecl2", command)

    def test_500_failmissingcluster(self):
        command = ["update_esx_cluster", "--cluster=cluster-does-not-exist",
                   "--comments=test should fail"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

    def test_600_updatethreshold(self):
        cname = "utecl7"
        command = ["update_esx_cluster", "--cluster=%s" % cname,
                   "--down_hosts_threshold=1%",
                   "--maint_threshold=50%"]
        out = self.successtest(command)

        ## verify show
        command = "show esx_cluster --cluster %s" % cname
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Down Hosts Threshold: 0 (1%)", command)
        self.matchoutput(out, "Maintenance Threshold: 2 (50%)", command)

        ## verify cat
        command = "cat --cluster=%s --data" % cname
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"system/cluster/down_hosts_threshold" = 0;',
                         command)
        self.matchoutput(out, '"system/cluster/down_maint_threshold" = 2;',
                         command)
        self.matchoutput(out, '"system/cluster/down_hosts_as_percent" = true;',
                         command)
        self.matchoutput(out, '"system/cluster/down_maint_as_percent" = true;',
                         command)
        self.matchoutput(out, '"system/cluster/down_hosts_percent" = 1;',
                         command)
        self.matchoutput(out, '"system/cluster/down_maint_percent" = 50;',
                         command)

    def test_605_compileforthreshold(self):
        cname = "utecl7"
        command = "compile --cluster=%s" % cname
        out = self.successtest(command.split(" "))

    # FIXME: Need tests for plenary templates
    # FIXME: Include test that machine plenary moved correctly


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
