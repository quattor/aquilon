#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
            # Deprecated.
            self.successtest(["update_esx_cluster", "--cluster=utecl%d" % i,
                              "--tor_switch=ut01ga2s01.aqd-unittest.ms.com"])
        for i in range(8, 11):
            self.noouttest(["update_esx_cluster", "--cluster=utecl%d" % i,
                            "--switch=ut01ga2s02.aqd-unittest.ms.com"])
        for i in range(11, 13):
            self.noouttest(["update_esx_cluster", "--cluster=utecl%d" % i,
                            "--switch=ut01ga2s03.aqd-unittest.ms.com"])
            self.noouttest(["update_esx_cluster", "--cluster=npecl%d" % i,
                            "--switch=np01ga2s03.one-nyp.ms.com"])

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

    def test_150_verifypg(self):
        for i in range(0, 8) + range(9, 17):
            if i < 9:
                port_group = "user-v71%d" % (i / 2)
            else:
                port_group = "user-v71%d" % ((i - 9) / 2)
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
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                port = i
                machine = "ut11s01p%d" % port
            else:
                port = i - 12
                machine = "ut12s02p%d" % port
            command = ["add", "auxiliary", "--auxiliary", hostname,
                       "--machine", machine, "--interface", "eth1", "--autoip"]
            self.noouttest(command)

    def test_210_verifyaux(self):
        command = ["search_system", "--type=auxiliary",
                   "--dns_domain=aqd-unittest.ms.com",
                   "--networkip", self.net.vm_storage_net[0].ip]
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
            port_group = "user-v71%d" % (i / 2)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, """"location" = "ut.ny.na";""", command)
            self.matchoutput(out,
                             """include { """
                             """'hardware/machine/utvendor/utmedium' };""",
                             command)
            self.matchoutput(out,
                             """"ram" = list(create("hardware/ram/generic", """
                             """"size", 8192*MB));""",
                             command)
            self.matchoutput(out,
                             """"cpu" = list(create("""
                             """"hardware/cpu/intel/xeon_2500"));""",
                             command)
            self.searchoutput(out,
                              r'"cards/nic/eth0" = nlist\(\s*'
                              r'"hwaddr", "00:50:56:[0-9a-f:]{8}",\s*'
                              r'"boot", true,\s*'
                              r'"port_group", "%s",\s*\);'
                              % port_group,
                              command)

    def test_600_makecluster(self):
        for i in range(5, 11):
            command = ["make_cluster", "--cluster=utecl%s" % i]
            (out, err) = self.successtest(command)

    def test_700_add_hosts(self):
        # Skip index 8 and 17 - these don't have interfaces.
        for i in range(0, 8) + range(9, 17):
            machine = "evm%d" % (10 + i)
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)
            command = ["add_host", "--hostname", hostname,
                       "--machine", machine, "--autoip", "--domain=unittest",
                       "--archetype=aquilon", "--personality=inventory",
                       "--osname=linux", "--osversion=4.0.1-x86_64"]
            (out, err) = self.successtest(command)

    def test_800_verify_add_host(self):
        for i in range(1, 9) + range(10, 18):
            if i < 10:
                net_index = ((i - 1) / 2) + 2
                usable_index = (i - 1) % 2
            else:
                net_index = ((i - 10) / 2) + 6
                usable_index = (i - 10) % 2
            hostname = "ivirt%d.aqd-unittest.ms.com" % i
            ip = self.net.unknown[net_index].usable[usable_index]
            command = "search host --hostname %s --ip %s" % (hostname, ip)
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, hostname, command)

    def test_900_make_hosts(self):
        for i in range(0, 8) + range(9, 17):
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)
            command = ["make", "--hostname", hostname]
            (out, err) = self.successtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAdd10GigHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
