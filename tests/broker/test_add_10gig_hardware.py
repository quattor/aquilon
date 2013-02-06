#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing commands that add virtual hardware."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

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

    def test_135_addmgddisks(self):
        for i in range(0, 8):
            share = "utecl%d_share" % (5 + (i / 3))
            machine = "evm%d" % (10 + i)
            #these get deleted in test_del_machine
            self.noouttest(["add", "disk", "--machine", machine,
                            "--disk", "sdb", "--controller", "sata",
                            "--size", "30", "--autoshare",
                            "--address", "0:0"])
            #these get deleted in test_del_disk
            self.noouttest(["add", "disk", "--machine", machine,
                            "--disk", "sdc", "--controller", "sata",
                            "--size", "30", "--autoshare",
                            "--address", "0:0"])

    def test_137_addmgddisks_badmgdshare(self):
        #try to add a managed share manually. should error.
        command = ["add", "disk", "--machine", "evm10",
                   "--disk", "sdf", "--controller", "sata",
                   "--size", "15", "--share", "utecl13_share",
                   "--address", "0:0"]
        out, err = self.failuretest(command, 4)
        self.matchoutput(err, "Bad Request: Disk 'utecl13_share' is managed by "
                         "resourcepool and can only be assigned with the "
                         "'autoshare' option.", command)

    def test_140_addmgddisks_badsize(self):
        #size 15 triggers the unsupported size error msg
        command = ["add", "disk", "--machine", "evm10",
                   "--disk", "sdd", "--controller", "sata",
                   "--size", "15", "--autoshare",
                   "--address", "0:0"]
        out, err = self.failuretest(command, 4)
        self.matchoutput(err,
                         "Bad Request: Invalid size for autoshare disk. "
                         "Supported sizes are: ['30, 40, 50']",
                         command)

    def test_145_addmgddisks_nocapacity(self):
        #id sde_evm10 triggers no capacity error
        command = ["add", "disk", "--machine", "evm10",
                   "--disk", "sde", "--controller", "sata",
                   "--size", "30", "--autoshare",
                   "--address", "0:0"]
        out, err = self.failuretest(command, 4)
        self.matchoutput(err,
                         "Bad Request: No available NAS capacity in "
                         "Resource Pool for rack ut11. Please notify an "
                         "administrator or add capacity.",
                         command)

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
        self.matchoutput(out, str(self.net.unknown[2]), command)

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
        net = self.net.vm_storage_net[0]
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
                   "--ip", self.net.vm_storage_net[0].ip]
        out = self.commandtest(command)
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            self.matchoutput(out, hostname, command)

    def test_300_delmachines(self):
        # Need to remove machines without interfaces or the make will fail.
        for i in [18, 27]:
            self.noouttest(["del", "machine", "--machine", "evm%d" % i])

    def test_400_norack(self):
        command = ["add", "disk", "--machine", "utnorack", "--disk", "sdb",
                   "--capacity", "150", "--controller", "scsi",
                   "--address", "0:0", "--autoshare"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine utnorack is not associated with a rack.",
                         command)

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
    # evm10 -> self.net.unknown[2].usable[0]
    # evm11 -> self.net.unknown[3].usable[0]
    # evm12 -> self.net.unknown[4].usable[0]
    # evm13 -> self.net.unknown[5].usable[0]
    # evm14 -> self.net.unknown[2].usable[1]
    # As each subnet only has two usable IPs, when we get to evm19 it becomes
    # evm19 -> self.net.unknown[6].usable[0]
    # and the above pattern repeats
    def test_700_add_hosts(self):
        # Skip index 8 and 17 - these don't have interfaces. Index 16 will be
        # used for --prefix testing.
        mac_prefix = "00:50:56:01:20"
        mac_idx = 60
        for i in range(0, 8) + range(9, 16):
            machine = "evm%d" % (10 + i)
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)

            if i < 9:
                net_index = (i % 4) + 2
                usable_index = i / 4
            else:
                net_index = ((i - 9) % 4) + 6
                usable_index = (i - 9) / 4
            ip = self.net.unknown[net_index].usable[usable_index]

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
        ip = self.net.unknown[9].usable[1]
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
        for i in range(0, 8) + range(9, 17):
            if i < 9:
                net_index = (i % 4) + 2
                usable_index = i / 4
            else:
                net_index = ((i - 9) % 4) + 6
                usable_index = (i - 9) / 4
            hostname = "ivirt%d.aqd-unittest.ms.com" % (i + 1)
            ip = self.net.unknown[net_index].usable[usable_index]
            command = "search host --hostname %s --ip %s" % (hostname, ip)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, hostname, command)

    def test_810_verify_audit(self):
        i = 16
        net_index = ((i - 9) % 4) + 6
        usable_index = (i - 9) / 4
        ip = self.net.unknown[net_index].usable[usable_index]
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
