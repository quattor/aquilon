#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the del host command."""

from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin
from machinetest import MachineTestMixin


class TestDelHost(VerifyNotificationsMixin, MachineTestMixin,
                  TestBrokerCommand):

    def test_100_del_unittest02(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[11])
        command = "del host --hostname unittest02.one-nyp.ms.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_105_verify_del_unittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_110_del_unittest00(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[2])
        command = "del host --hostname unittest00.one-nyp.ms.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_115_verify_del_unittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_115_verify_del_unittest00_dns(self):
        command = "show address --fqdn unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_115_verify_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        # The primary name must be gone
        self.matchclean(out, "Primary Name:", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)
        # No interface should have the IP address
        self.matchclean(out, "Auxiliary:", command)
        self.matchclean(out, "Provides:", command)
        self.matchclean(out, str(self.net["unknown0"].usable[2]), command)

    # unittest01.one-nyp.ms.com gets deleted in test_del_windows_host.

    def test_120_del_aurora_with_node(self):
        command = "del host --hostname %s.ms.com" % self.aurora_with_node
        err = self.statustest(command.split(" "))
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_with_node,
                         command)

    def test_121_verify_del_aurora_with_node(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        self.notfoundtest(command.split(" "))

    def test_125_del_aurora_without_node(self):
        command = "del host --hostname %s.ms.com" % self.aurora_without_node
        err = self.statustest(command.split(" "))
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_without_node,
                         command)

    def test_126_verify_del_aurora_without_node(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        self.notfoundtest(command.split(" "))

    def test_130_del_aurora_without_rack(self):
        command = "del host --hostname %s.ms.com" % self.aurora_without_rack
        err = self.statustest(command.split(" "))
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_without_rack,
                         command)

    def test_131_verify_del_aurora_without_rack(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_rack
        self.notfoundtest(command.split(" "))

    def test_140_del_nyaqd1(self):
        command = "del host --hostname nyaqd1.ms.com"
        self.statustest(command.split(" "))

    def test_140_verify_del_nyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        self.notfoundtest(command.split(" "))

    def test_150_del_aurora_default_os(self):
        command = "del host --hostname test-aurora-default-os.ms.com --quiet"
        self.noouttest(command.split(" "))
        self.dsdb_verify(empty=True)

    def test_151_verify_del_aurora_default_os(self):
        command = "show host --hostname test-aurora-default-os.ms.com"
        self.notfoundtest(command.split(" "))

    def test_155_del_windows_default_os(self):
        ip = self.net["tor_net_0"].usable[5]
        self.dsdb_expect_delete(ip)
        command = "del host --hostname test-windows-default-os.msad.ms.com --quiet"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_156_verify_del_windows_default_os(self):
        command = "show host --hostname test-windows-default-os.msad.ms.com"
        self.notfoundtest(command.split(" "))

    def test_160_del_jack(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[17])
        command = "del host --hostname jack.cards.example.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_165_verify_del_jack(self):
        command = "show host --hostname jack.cards.example.ms.com"
        self.notfoundtest(command.split(" "))

    def test_170_unbind_notify(self):
        hostname = self.config.get("unittest", "hostname")
        command = ["unbind", "server", "--service", "utnotify",
                   "--instance", "localhost", "--hostname", hostname]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Warning: Host %s is missing the following required "
                         "services" % hostname,
                         command)

    def test_171_del_notify(self):
        hostname = self.config.get("unittest", "hostname")
        self.dsdb_expect_delete("127.0.0.1")
        basetime = datetime.now()
        command = ["del", "host", "--hostname", hostname]
        self.statustest(command)
        self.wait_notification(basetime, 0)
        self.dsdb_verify()

    def test_300_del_afsbynet(self):
        self.delete_host("afs-by-net.aqd-unittest.ms.com",
                         self.net["netsvcmap"].usable[0], "ut3c5n11")

    def test_300_del_netmappers(self):
        self.delete_host("netmap-pers.aqd-unittest.ms.com",
                         self.net["netperssvcmap"].usable[0], "ut3c5n12")

    def test_300_del_unittest12(self):
        self.delete_host("unittest12.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[7], "ut3s01p1")

    def test_300_del_unittest15(self):
        self.delete_host("unittest15.aqd-unittest.ms.com",
                         self.net["tor_net_0"].usable[1], "ut8s02p1")

    def test_300_del_unittest16(self):
        self.delete_host("unittest16.aqd-unittest.ms.com",
                         self.net["tor_net_0"].usable[2], "ut8s02p2")

    def test_300_del_unittest17(self):
        self.delete_host("unittest17.aqd-unittest.ms.com",
                         self.net["tor_net_0"].usable[3], "ut8s02p3")

    def test_300_del_unittest18(self):
        self.delete_host("unittest18.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[18], "ut3c1n8")

    def test_300_del_unittest20(self):
        # The transits are deleted in test_del_interface_address
        self.delete_host("unittest20.aqd-unittest.ms.com",
                         self.net["zebra_vip"].usable[2], "ut3c5n2")

    def test_300_del_unittest21(self):
        self.delete_host("unittest21.aqd-unittest.ms.com",
                         self.net["zebra_eth0"].usable[1], "ut3c5n3")

    def test_300_del_unittest22(self):
        self.delete_host("unittest22.aqd-unittest.ms.com",
                         self.net["zebra_eth0"].usable[2], "ut3c5n4")

    def test_300_del_unittest23(self):
        self.delete_host("unittest23.aqd-unittest.ms.com",
                         self.net["vpls"].usable[1], "ut3c5n5")

    def test_300_del_unittest24(self):
        self.delete_host("unittest24.aqd-unittest.ms.com",
                         self.net["vpls"].usable[2], "np3c5n5")

    def test_300_del_unittest25(self):
        self.delete_host("unittest25.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[20], "ut3c5n7")

    def test_300_del_unittest26(self):
        self.delete_host("unittest26.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[23], "ut3c5n8")

    def test_300_del_filer(self):
        self.delete_host("filer1.ms.com", self.net["vm_storage_net"].usable[25],
                         "filer1")

    def test_300_del_f5test(self):
        self.delete_host("f5test.aqd-unittest.ms.com", self.net["f5test"].ip,
                         "f5test")

    def test_300_del_utinfra(self):
        eth0_ip = self.net["unknown0"].usable[33]
        eth1_ip = self.net["unknown1"].usable[34]
        ip = self.net["zebra_vip"].usable[3]
        self.delete_host("infra1.aqd-unittest.ms.com", ip, "ut3c5n13",
                         interfaces=["eth0", "eth1"],
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_300_del_npinfra(self):
        eth0_ip = self.net["unknown0"].usable[35]
        eth1_ip = self.net["unknown1"].usable[36]
        ip = self.net["zebra_vip"].usable[4]
        self.delete_host("infra1.one-nyp.ms.com", ip, "np3c5n13",
                         interfaces=["eth0", "eth1"],
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_300_del_hp_rack_hosts(self):
        servers = 0
        net = self.net["hp_eth0"]
        for i in range(51, 100):
            port = i - 50
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            machine = "ut9s03p%d" % port
            self.delete_host(hostname, net.usable[port], machine)

    def test_300_del_verari_rack_hosts(self):
        net = self.net["verari_eth0"]
        for i in range(101, 111):
            port = i - 100
            hostname = "evh%d.aqd-unittest.ms.com" % port
            machine = "ut10s04p%d" % port
            self.delete_host(hostname, net.usable[port], machine)

    def test_300_del_10gig_rack_hosts(self):
        net = self.net["vmotion_net"]
        for i in range(1, 25):
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                machine = "ut11s01p%d" % i
            else:
                machine = "ut12s02p%d" % (i - 12)
            self.delete_host(hostname, net.usable[i + 1], machine)

    def test_300_del_esx_bcp_cluster_hosts(self):
        for port in range(1, 25):
            for rack, domain, net in [("ut13", "aqd-unittest.ms.com", self.net["esx_bcp_ut"]),
                                      ("np13", "one-nyp.ms.com", self.net["esx_bcp_np"])]:
                hostname = "evh%d.%s" % (port + 74, domain)
                machine = "%ss03p%d" % (rack, port)
                self.delete_host(hostname, net.usable[port], machine)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
