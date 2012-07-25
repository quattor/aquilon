#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
"""Module for testing the vulcan2 related commands."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestVulcan20(TestBrokerCommand):


    # Metacluster / cluster / Switch tests


    def test_000_addutmc8(self):
        command = ["add_metacluster", "--metacluster=utmc8",
                   "--personality=vulcan2-test", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut", "--domain=unittest",
                   "--comments=autopg_v2_tests"]
        self.noouttest(command)

    def add_utcluster(self, name, metacluster):
        command = ["add_esx_cluster", "--cluster=%s" % name,
                   "--metacluster=%s" % metacluster, "--building=ut",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan2-10g-test"]
        self.noouttest(command)

    # see testaddutmc4
    def test_001_addutpgcl(self):
        # Allocate utecl5 - utecl10 for utmc4 (autopg testing)
        for i in range(0, 2):
            self.add_utcluster("utpgcl%d" % i, "utmc8")

    # see     def testaddut01ga2s02(self):
    def test_002_addutpgsw(self):
        # Deprecated.

        for i in range(0, 2):
            ip = self.net.unknown[17].usable[i]
            hostname = "utpgsw%d.aqd-unittest.ms.com" % i

            self.dsdb_expect_add(hostname, ip, "xge49",
                                 ip.mac)
            command = ["add", "tor_switch",
                       "--tor_switch", hostname,
                       "--building", "ut", "--rackid", "12",
                       "--rackrow", "k", "--rackcol", "2",
                       "--model", "rs g8000", "--interface", "xge49",
                       "--mac", ip.mac, "--ip", ip]
            (out, err) = self.successtest(command)
        self.dsdb_verify()

    # see     def testverifypollut01ga2s01(self):
    # see fakevlan2net
    def test_003_pollutpgsw(self):
        # Issues deprecated warning.
        for i in range(0, 2):
            command = ["poll", "switch", "--vlan", "--switch",
                       "utpgsw%d.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)

            service = self.config.get("broker", "poll_helper_service")
            self.matchoutput(err,
                             "Using jump host nyaqd1.ms.com from service "
                             "instance %s/unittest to run CheckNet "
                             "for switch utpgsw%d.aqd-unittest.ms.com" %
                             (service, i),
                             command)

    # for each cluster's hosts
    def test_004_add10gigracks(self):
        for port in range(0, 2):
            self.noouttest(["add", "machine", "--machine", "utpgs01p%d" % port,
                            "--rack", "ut11", "--model", "vb1205xm"])

    def test_005_add10gigrackinterfaces(self):
        for i in range(0, 2):
            ip = self.net.unknown[18].usable[i]
            machine = "utpgs01p%d" % i

            self.noouttest(["add", "interface", "--interface", "eth0",
                            "--machine", machine,
                            "--mac", ip.mac])

    def test_006_populate10gigrackhosts(self):
        for i in range(0, 2):
            ip = self.net.unknown[18].usable[i]
            hostname = "utpgh%d.aqd-unittest.ms.com" % i
            machine = "utpgs01p%d" % i

            self.dsdb_expect_add(hostname, ip, "eth0", ip.mac)
            command = ["add", "host", "--hostname", hostname, "--ip", ip,
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan2-10g-test"]
            self.noouttest(command)
        self.dsdb_verify()

    def test_007_makeclusters(self):
        for i in range(0, 2):

            host = "utpgh%s.aqd-unittest.ms.com" % i
            cluster = "utpgcl%d" % i
            self.successtest(["make", "cluster", "--cluster", cluster])

            self.successtest(["cluster",
                              "--hostname", host, "--cluster", cluster])

    def test_008_addmachines(self):
        for i in range(0, 3):
            cluster = "utpgcl%d" % (i / 2)
            machine = "utpgm%d" % i

            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", cluster, "--model", "utmedium"])

    def test_009_addswitch(self):
        for i in range(0, 2):
            self.successtest(["update_esx_cluster", "--cluster=utpgcl%d" % i,
                              "--switch=utpgsw%d.aqd-unittest.ms.com" % i])

    def test_010_addstorageips(self):
        # storage IPs
        for i in range(0, 2):
            ip = self.net.vm_storage_net[0].usable[i + 26]
            machine = "utpgs01p%d" % i

            self.noouttest(["add", "interface", "--interface", "eth1",
                            "--machine", machine,
                            "--mac", ip.mac])

            self.dsdb_expect_add("utpgh%d-eth1.aqd-unittest.ms.com" % i,
                                 ip, "eth1", ip.mac,
                                 primary="utpgh%d.aqd-unittest.ms.com" % i)
            command = ["add", "interface", "address", "--machine", machine,
                       "--interface", "eth1", "--ip", ip]
            self.noouttest(command)
        self.dsdb_verify()


    # Autopg test
    def test_100_addinterfaces(self):
        # These ones fit the 2 address net
        for i in range(0, 2):
            machine = "utpgm%d" % i
            self.noouttest(["add", "interface", "--machine", machine,
                            "--interface", "eth0", "--automac", "--autopg"])

        # The third one shall fail
        command = ["add", "interface", "--machine", "utpgm%d" % 2,
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on switch "
                         "utpgsw1.aqd-unittest.ms.com",
                         command)




#    Storage group / resource tests


    def test_101_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--required_type=share"]
        self.successtest(command)

        command = ["show_resourcegroup", "--cluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Bound to: ESX Metacluster utmc8", command)

        command = ["add_resourcegroup", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--required_type=share"]
        self.successtest(command)

        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Resource Group: utmc8as2", command)

    def test_102_verify_metacluster(self):
        self.successtest(["make", "cluster", "--cluster", "utmc8"])

        command = ["cat", "--cluster", "utmc8", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"/system/resources/resourcegroup" = '
                         'push(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as1/config"));',
                         command)


    def test_103_add_share_to_rg(self):
        command = ["add_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share",
                   "--latency=5"]
        self.successtest(command)

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Latency: 5", command)

        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--share=test_v2_share",
                   "--latency=5"]
        self.successtest(command)

        command = ["show_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as2", command)

    def test_104_add_same_share_name_fail(self):
        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--share=test_v2_share", "--latency=5"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: Share test_v2_share, "
                         "bundleresource instance already exists.", command)

    def test_105_cat_rg(self):
        command = ["cat", "--resourcegroup=utmc8as1", "--cluster=utmc8",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/config;",
                         command)
        self.matchoutput(out, '"name" = "utmc8as1', command)
        self.matchoutput(out,
                         '"resources/share" = '
                         'push(create("resource/cluster/utmc8/resourcegroup/'
                         'utmc8as1/share/test_v2_share/config"));',
                         command)

        # TODO no resources, waiting for big resource branch

    def test_106_cat_share(self):
        command = ["cat", "--share=test_v2_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/share/test_v2_share/config;",
                         command)
        self.matchoutput(out, '"name" = "test_v2_share";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_v2_share";',
                         command)
        self.matchoutput(out, '"latency" = 5;', command)

    def test_107_cat_switch(self):
        for i in range(0, 2):
            command = ["cat", "--switch", "utpgsw%d" % i]

            out = self.commandtest(command)
            self.matchoutput(out, '"user-v710", nlist(', command)

    def test_108_addutpgm0disk(self):
        self.noouttest(["add", "disk", "--machine", "utpgm0",
            "--disk", "sdb", "--controller", "scsi", "--share", "test_v2_share",
            "--size", "34", "--resourcegroup", "utmc8as1", "--address", "0:0"])

    def test_109_verifyaddutpgm0disk(self):
        command = "show machine --machine utpgm0"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Disk: sdb 34 GB scsi "
                          "\(virtual_disk from test_v2_share\)$", command)

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.searchoutput(out, r"Disk: sdb 34 GB \(Machine: utpgm0\)$", command)

    def test_111_addfilesystemfail(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--resourcegroup=utmc8as1"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: Resource's filesystem type "
                         "differs from the requested share",
                         command)

    def test_112_verify_rg(self):
        command = ["show_resourcegroup", "--cluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_113_verifyutmc8(self):
        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_114_share(self):
        command = ["search_machine", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utpgm0", command)
        self.matchclean(out, "evm2", command)
        self.matchclean(out, "evm10", command)

    def test_115_search_host_by_metacluster(self):
        command = "search host --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgh0.aqd-unittest.ms.com", command)
        self.matchoutput(out, "utpgh1.aqd-unittest.ms.com", command)

    def test_116_search_machine_by_metacluster(self):
        command = "search machine --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgm0", command)
        self.matchoutput(out, "utpgm1", command)
        self.matchoutput(out, "utpgm2", command)
        self.matchclean(out, "utpgs01p0", command)

#    metacluster aligned svc tests

    def test_150_addvcenterservices(self):
        command = ["add", "service", "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

        command = ["add", "service", "--service", "vcenter", "--instance", "np"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-10g-test"]
        self.noouttest(command)

        command = ["add_cluster_aligned_service", "--cluster_type", "meta",
                   "--service", "vcenter"]
        self.noouttest(command)

    def test_150_failaddvcenteragain(self):
        command = ["add_cluster_aligned_service", "--cluster_type", "meta",
                   "--service", "vcenter"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Service vcenter is already aligned to "
                         "ESX metaclusters.", command)


    def test_151_mapvcenterservices(self):
        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut", "--personality", "vulcan2-10g-test",
                   "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "np",
                   "--building", "np", "--personality", "vulcan2-10g-test",
                   "--archetype", "vmhost"]
        self.noouttest(command)


    def test_152_bindvcenterservices(self):
        command = ["bind_cluster", "--cluster", "utmc8", "--service", "vcenter",
                   "--instance", "ut"]
        err = self.statustest(command)
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service vcenter instance ut", command)

        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host utpgh0.aqd-unittest.ms.com adding binding "
                         "for service vcenter instance ut", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Template: service/vcenter/ut", command)

        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Member Alignment: Service vcenter Instance ut", command)

    def test_152_failmaxclientcount(self):
        command = ["update_service", "--service", "vcenter", "--instance", "ut",
                   "--max_clients", "17"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut"]
        self.noouttest(command)

        self.add_utcluster("utpgcl2", "utmc8")

        command = ["make", "cluster", "--cluster", "utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The available instances ['ut'] for service vcenter "
                         "are at full capacity.",
                         command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut"]
        self.noouttest(command)

        command = ["del_esx_cluster", "--cluster=utpgcl2"]
        self.successtest(command)

    def test_153_unbindvcenterservices(self):
        command = ["del_cluster_aligned_service", "--cluster_type", "meta",
                   "--service", "vcenter"]
        self.noouttest(command)

        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-10g-test"]
        self.noouttest(command)

        command = ["unbind_cluster", "--cluster", "utmc8",
                   "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

    def test_154_unmapvcenterservices(self):
        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut",
                   "--personality", "vulcan2-10g-test", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "np", "--building", "np",
                   "--personality", "vulcan2-10g-test", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host utpgh0.aqd-unittest.ms.com removing "
                         "binding for service vcenter instance ut", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Template: service/vcenter/ut", command)

    def test_155_delvcenterservices(self):
        command = ["del", "service", "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

        command = ["del", "service", "--service", "vcenter", "--instance", "np"]
        self.noouttest(command)

#
##    service binding conflicts
#
    def test_170_add_mc_esx_service(self):
        command = ["add", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["add_cluster_aligned_service", "--service", "esx_management_server",
                   "--cluster_type", "meta"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2-test",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["bind_cluster", "--cluster", "utmc8", "--service", "esx_management_server",
                   "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service esx_management_server instance ut.mc", command)

    def test_170_fail_make_host(self):
        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Replacing ut.a instance with ut.mc (bound to "
                         "ESX metacluster utmc8) for service esx_management_server",
                         command)
        self.matchoutput(out,
                         "ESX Cluster utpgcl0 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for utpgh0.aqd-unittest.ms.com.",
                         command)

    def test_175_verify_client_count(self):
        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 16$", command)

    def test_175_verify_mixed_client_count(self):
        self.add_utcluster("utpgcl3", "utmc8")
        command = ["bind_cluster", "--cluster", "utpgcl3", "--service",
                   "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "ESX Cluster utpgcl3 adding binding for service "
                         "esx_management_server instance ut.mc", command)

        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 24$", command)

        # Can't unbind an an aligned service here and don't want unalign it

        command = ["del_esx_cluster", "--cluster=utpgcl3"]
        self.successtest(command)

    def test_180_remove_mc_esx_service(self):
        command = ["del_cluster_aligned_service", "--service", "esx_management_server",
                   "--cluster_type", "meta"]
        self.noouttest(command)

        command = ["unbind_cluster", "--cluster", "utmc8", "--service", "esx_management_server",
                   "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2-test",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["del", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)


#    Storage group related deletes


    def test_202_delutpgm0disk(self):
        self.noouttest(["del", "disk", "--machine", "utpgm0",
            "--controller", "scsi", "--disk", "sdb"])

    def test_204_delresourcegroup(self):
        command = ["del_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8"]
        self.successtest(command)

        command = ["del_share", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8"]
        self.successtest(command)


    # Metacluster / cluster / Switch deletes


    def test_305_delinterfaces(self):
        for i in range(0, 2):
            ip = self.net.vm_storage_net[0].usable[i + 26]
            machine = "utpgs01p%d" % i

            self.dsdb_expect_delete(ip)
            command = ["del", "interface", "address", "--machine", machine,
                       "--interface", "eth1", "--ip", ip]
            self.noouttest(command)

            self.noouttest(["del", "interface", "--interface", "eth1",
                            "--machine", machine])
        self.dsdb_verify()

    def test_306_delmachines(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            self.noouttest(["del", "machine", "--machine", machine])

    def test_307_del10gigrackhosts(self):
        for i in range(0, 2):
            ip = self.net.unknown[18].usable[i]
            hostname = "utpgh%d.aqd-unittest.ms.com" % i

            self.dsdb_expect_delete(ip)
            command = ["del", "host", "--hostname", hostname]
            (out, err) = self.successtest(command)
            self.matchoutput(err, "sent 1 server notifications", command)
        self.dsdb_verify()

    def test_307_del10gigracks(self):
        for port in range(0, 2):
            self.noouttest(["del", "machine", "--machine",
                            "utpgs01p%d" % port])

    def test_308_delutpgsw(self):
        for i in range(0, 2):
            ip = self.net.unknown[17].usable[i]

            self.dsdb_expect_delete(ip)
            swname = "utpgsw%d.aqd-unittest.ms.com" % i
            command = "del switch --switch %s" % swname
            self.noouttest(command.split(" "))

            plenary = os.path.join(self.config.get("broker", "plenarydir"),
                       "switchdata", "%s.tpl" % swname)
            self.failIf(os.path.exists(plenary),
                        "Plenary file '%s' still exists" % plenary)

        self.dsdb_verify()

    def test_309_delutpgcl(self):
        command = ["del_metacluster", "--metacluster=utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "ESX Metacluster utmc8 is still in use by "
                         "clusters: utpgcl0, utpgcl1.", command)

        for i in range(0, 2):
            command = ["del_esx_cluster", "--cluster=utpgcl%d" % i]
            self.successtest(command)

    def test_310_delutmc8(self):
        command = ["del_metacluster", "--metacluster=utmc8"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 1 server notifications", command)

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utmc8%s" % self.profile_suffix)))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcan20)
    unittest.TextTestRunner(verbosity=2).run(suite)
