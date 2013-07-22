#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing commands that add virtual hardware."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAdd10GigHardware(TestBrokerCommand):

    def test_000_addmachines(self):
        for i in range(0, 18):
            cluster = "utecl%d" % (5 + (i / 3))
            machine = "evm%d" % (10 + i)
            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", cluster, "--model", "utmedium"])

    def test_005_failsearchnetwork(self):
        command = ["search_network", "--machine=evm18"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine evm18 has no interfaces with a portgroup or "
                         "assigned to a network.",
                         command)

    def test_010_oldlocation(self):
        for i in range(5, 11):
            command = ["show_esx_cluster", "--cluster=utecl%d" % i]
            out = self.commandtest(command)
            self.matchoutput(out, "Building: ut", command)

    def test_020_fixlocation(self):
        for i in range(5, 11):
            command = ["update_esx_cluster", "--cluster=utecl%d" % i,
                       "--fix_location"]
            self.noouttest(command)

    def test_025_fixlocation(self):
        for i in range(11, 13):
            for building in ["np", "ut"]:
                cluster = "%secl%d" % (building, i)
                self.noouttest(["update_esx_cluster", "--cluster", cluster,
                                "--fix_location"])

    def test_030_newlocation(self):
        for i in range(5, 8):
            command = ["show_esx_cluster", "--cluster=utecl%d" % i]
            out = self.commandtest(command)
            self.matchoutput(out, "Rack: ut11", command)
        for i in range(8, 11):
            command = ["show_esx_cluster", "--cluster=utecl%d" % i]
            out = self.commandtest(command)
            self.matchoutput(out, "Rack: ut12", command)

    def test_090_addswitch(self):
        for i in range(5, 8):
            self.successtest(["update_esx_cluster", "--cluster=utecl%d" % i,
                              "--switch=ut01ga2s01.aqd-unittest.ms.com"])
        for i in range(8, 11):
            self.noouttest(["update_esx_cluster", "--cluster=utecl%d" % i,
                            "--switch=ut01ga2s02.aqd-unittest.ms.com"])
        for i in range(11, 13):
            self.noouttest(["update_esx_cluster", "--cluster=utecl%d" % i,
                            "--switch=ut01ga2s03.aqd-unittest.ms.com"])
            self.noouttest(["update_esx_cluster", "--cluster=npecl%d" % i,
                            "--switch=np01ga2s03.one-nyp.ms.com"])

    def test_095_unused_pg(self):
        # If
        # - the machine has a host defined,
        # - the host is in a cluster,
        # - and the cluster has a switch,
        # then setting an invalid port group is an error.
        # TODO: why is this not an error if the above conditions do not hold?
        command = ["add", "interface", "--machine", "evh51.aqd-unittest.ms.com",
                   "--interface", "eth2", "--pg", "unused-v999"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "VLAN 999 not found for switch ut01ga2s01.aqd-unittest.ms.com.",
                         command)

    def test_100_addinterfaces(self):
        # Skip index 8 and 17 - these will fail.
        for i in range(0, 8) + range(9, 17):
            machine = "evm%d" % (10 + i)
            self.noouttest(["add", "interface", "--machine", machine,
                            "--interface", "eth0", "--automac", "--autopg"])

    def test_110_failnopg(self):
        command = ["add", "interface", "--machine", "evm18",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on switch "
                         "ut01ga2s01.aqd-unittest.ms.com",
                         command)

    def test_111_failnopg(self):
        command = ["add", "interface", "--machine", "evm27",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on switch "
                         "ut01ga2s02.aqd-unittest.ms.com",
                         command)

    def test_130_adddisks(self):
        for i in range(0, 18):
            share = "utecl%d_share" % (5 + (i / 3))
            machine = "evm%d" % (10 + i)
            self.noouttest(["add", "disk", "--machine", machine,
                            "--disk", "sda", "--controller", "sata",
                            "--size", "15", "--share", share,
                            "--address", "0:0"])

    # We are checking the portgroups the machines have been mapped to
    # evm10 -> user-v710, evm11 -> user-v711, evm12 -> user-v712, evm13 -> user-v13
    # evm14 -> user-v710, evm15 -> user-v711, evm16 -> user-v712, evm17 -> user-v13
    # and so on and so forth

    def test_150_verifypg(self):
        for i in range(0, 8) + range(9, 17):
            if i < 9:
                port_group = "user-v71%d" % (i % 4)
            else:
                port_group = "user-v71%d" % ((i - 9) % 4)
            machine = "evm%d" % (i + 10)
            command = ["search_machine", "--machine", machine,
                       "--pg", port_group]
            out = self.commandtest(command)
            self.matchoutput(out, machine, command)

    # Utility method...
    def verifypg(self):
        command = ["search_machine", "--machine=evm10", "--pg=user-v710"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm10", command)

    def test_155_verifysearch(self):
        command = ["search_network", "--machine=evm10"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["ut01ga2s01_v710"]), command)

    def test_160_updatenoop(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", "user-v710"]
        self.noouttest(command)
        self.verifypg()

    def test_165_updateclear(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", ""]
        self.noouttest(command)
        command = ["show_machine", "--machine=evm10"]
        out = self.commandtest(command)
        self.matchclean(out, "Port Group", command)

    def test_170_updatemanual(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", "user-v710"]
        self.noouttest(command)
        self.verifypg()

    def test_175_updateauto(self):
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--pg", ""]
        self.noouttest(command)
        command = ["update_interface", "--machine=evm10", "--interface=eth0",
                   "--autopg"]
        self.noouttest(command)
        self.verifypg()

    def test_200_addaux(self):
        net = self.net["vm_storage_net"]
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                port = i
                machine = "ut11s01p%d" % port
            else:
                port = i - 12
                machine = "ut12s02p%d" % port
            self.dsdb_expect_add(hostname, net.usable[i - 1],
                                 "eth1", net.usable[i - 1].mac,
                                 "evh%d.aqd-unittest.ms.com" % (i + 50))
            command = ["add", "auxiliary", "--auxiliary", hostname,
                       "--machine", machine, "--interface", "eth1", "--autoip"]
            self.noouttest(command)
        self.dsdb_verify()

    def test_210_verifyaux(self):
        command = ["show", "network", "--hosts",
                   "--ip", self.net["vm_storage_net"].ip]
        out = self.commandtest(command)
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            self.matchoutput(out, hostname, command)

    def test_300_delmachines(self):
        # Need to remove machines without interfaces or the make will fail.
        for i in [18, 27]:
            self.noouttest(["del", "machine", "--machine", "evm%d" % i])

    def test_500_verifycatmachines(self):
        for i in range(0, 8):
            command = "cat --machine evm%s" % (10 + i)
            port_group = "user-v71%d" % (i % 4)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, """"location" = "ut.ny.na";""", command)
            self.matchoutput(out,
                             'include { "hardware/machine/utvendor/utmedium" };',
                             command)
            self.searchoutput(out,
                              r'"ram" = list\(\s*'
                              r'create\("hardware/ram/generic",\s*'
                              r'"size", 8192\*MB\s*\)\s*\);',
                              command)
            self.searchoutput(out,
                              r'"cpu" = list\(\s*'
                              r'create\("hardware/cpu/intel/xeon_5150"\)\s*\);',
                              command)
            self.searchoutput(out,
                              r'"cards/nic" = nlist\(\s*'
                              r'"eth0", create\("hardware/nic/utvirt/default",\s*'
                              r'"boot", true,\s*'
                              r'"hwaddr", "00:50:56:[0-9a-f:]{8}",\s*'
                              r'"port_group", "%s"\s*\)\s*\);'
                              % port_group,
                              command)

    def test_600_makecluster(self):
        for i in range(5, 11):
            command = ["make_cluster", "--cluster=utecl%s" % i]
            (out, err) = self.successtest(command)

    # Because the machines are allocated across portgroups, the IP addresses
    # allocated by autoip also differ
    # evm10 -> self.net["ut01ga2s01_v710"].usable[0]
    # evm11 -> self.net["ut01ga2s01_v711"].usable[0]
    # evm12 -> self.net["ut01ga2s01_v712"].usable[0]
    # evm13 -> self.net["ut01ga2s01_v713"].usable[0]
    # evm14 -> self.net["ut01ga2s01_v710"].usable[1]
    # As each subnet only has two usable IPs, when we get to evm19 it becomes
    # evm19 -> self.net["ut01ga2s02_v710"].usable[0]
    # and the above pattern repeats
    def test_700_add_hosts(self):
        # Skip index 8 and 17 - these don't have interfaces. Index 16 will be
        # used for --prefix testing.
        mac_prefix = "00:50:56:01:20"
        mac_idx = 60
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        for i in range(0, 8) + range(9, 16):
            machine = "evm%d" % (10 + i)
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)

            if i < 9:
                net_index = (i % 4)
                usable_index = i / 4
            else:
                net_index = ((i - 9) % 4) + 4
                usable_index = (i - 9) / 4
            ip = nets[net_index].usable[usable_index]

            # FIXME: the MAC check is fragile...
            self.dsdb_expect_add(hostname, ip, "eth0",
                                 "%s:%02x" % (mac_prefix, mac_idx))
            mac_idx += 1

            command = ["add_host", "--hostname", hostname,
                       "--machine", machine, "--autoip", "--domain=unittest",
                       "--archetype=aquilon", "--personality=inventory",
                       "--osname=linux", "--osversion=5.0.1-x86_64"]
            (out, err) = self.successtest(command)
        self.dsdb_verify()

    def test_705_add_nexthost(self):
        ip = self.net["ut01ga2s02_v713"].usable[1]
        mac = "00:50:56:01:20:4b"
        self.dsdb_expect_add("ivirt17.aqd-unittest.ms.com", ip, "eth0", mac)
        command = ["add", "host", "--prefix", "ivirt", "--machine", "evm26",
                   "--autoip", "--domain", "unittest",
                   "--archetype", "aquilon", "--personality", "inventory",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64"]
        out = self.commandtest(command)
        # This also verifies that we use the mapping for the building, not the
        # city
        self.matchoutput(out, "ivirt17.aqd-unittest.ms.com", command)
        self.dsdb_verify()

    def test_710_bad_pg(self):
        command = ["add", "interface", "--machine", "ivirt1.aqd-unittest.ms.com",
                   "--interface", "eth1", "--pg", "unused-v999"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot verify port group availability: no record "
                         "for VLAN 999 on switch ut01ga2s01.aqd-unittest.ms.com.",
                         command)

    # This is verifying test_700, so logic applies for determing
    # the IP addresses autoIP will give out
    def test_800_verify_add_host(self):
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        for i in range(0, 8) + range(9, 17):
            if i < 9:
                net_index = (i % 4)
                usable_index = i / 4
            else:
                net_index = ((i - 9) % 4) + 4
                usable_index = (i - 9) / 4
            hostname = "ivirt%d.aqd-unittest.ms.com" % (i + 1)
            ip = nets[net_index].usable[usable_index]
            command = "search host --hostname %s --ip %s" % (hostname, ip)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, hostname, command)

    def test_810_verify_audit(self):
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        i = 16
        net_index = ((i - 9) % 4) + 4
        usable_index = (i - 9) / 4
        ip = nets[net_index].usable[usable_index]
        command = ["search", "audit", "--keyword",
                   "ivirt%d.aqd-unittest.ms.com" % (i + 1)]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "[Result: hostname=ivirt%d.aqd-unittest.ms.com "
                         "ip=%s]" % (i + 1, ip),
                         command)

    def test_900_make_hosts(self):
        for i in range(0, 8) + range(9, 17):
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)
            command = ["make", "--hostname", hostname]
            (out, err) = self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAdd10GigHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
