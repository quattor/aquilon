#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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
"""Module for testing the update_service_address command."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestUpdateServiceAddress(TestBrokerCommand):

    def test_100_remove_eth1(self):
        self.noouttest(["update_service_address",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--name", "hostname", "--interfaces", "eth0"])

    def test_101_verify_eth1_removed(self):
        ip = self.net["zebra_vip"].usable[2]
        eth0_ip = self.net["zebra_eth0"].usable[0]
        eth1_ip = self.net["zebra_eth1"].usable[0]
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r"Interface: eth0 %s \[boot, default_route\]" %
                          eth0_ip.mac, command)
        self.searchoutput(out, r"Interface: eth1 %s \[default_route\]" %
                          eth1_ip.mac, command)
        self.searchoutput(out,
                          r"Service Address: hostname\s*"
                          r"Address: unittest20.aqd-unittest.ms.com \[%s\]\s*"
                          r"Interfaces: eth0$" % ip,
                          command)

    def test_102_change_interface(self):
        self.noouttest(["update_service_address",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--name", "hostname", "--interfaces", "eth1"])

    def test_103_verify_change(self):
        ip = self.net["zebra_vip"].usable[2]
        eth0_ip = self.net["zebra_eth0"].usable[0]
        eth1_ip = self.net["zebra_eth1"].usable[0]
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r"Interface: eth0 %s \[boot, default_route\]" %
                          eth0_ip.mac, command)
        self.searchoutput(out, r"Interface: eth1 %s \[default_route\]" %
                          eth1_ip.mac, command)
        self.searchoutput(out,
                          r"Service Address: hostname\s*"
                          r"Address: unittest20.aqd-unittest.ms.com \[%s\]\s*"
                          r"Interfaces: eth1$" % ip,
                          command)

    def test_104_add_back_both(self):
        self.noouttest(["update_service_address",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--name", "hostname", "--interfaces", "eth0, eth1"])

    def test_105_verify_both(self):
        ip = self.net["zebra_vip"].usable[2]
        eth0_ip = self.net["zebra_eth0"].usable[0]
        eth1_ip = self.net["zebra_eth1"].usable[0]
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r"Interface: eth0 %s \[boot, default_route\]" %
                          eth0_ip.mac, command)
        self.searchoutput(out, r"Interface: eth1 %s \[default_route\]" %
                          eth1_ip.mac, command)
        self.searchoutput(out,
                          r"Service Address: hostname\s*"
                          r"Address: unittest20.aqd-unittest.ms.com \[%s\]\s*"
                          r"Interfaces: eth0, eth1$" % ip,
                          command)

    def test_110_update_zebra3(self):
        new_ip = self.net["zebra_vip"].usable[6]
        self.dsdb_expect_update("zebra3.aqd-unittest.ms.com", ip=new_ip,
                                comments="New service address comments")
        self.noouttest(["update_service_address",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--name", "zebra3", "--ip", new_ip,
                        "--nomap_to_primary",
                        "--comments", "New service address comments"])
        self.dsdb_verify()

    def test_111_verify_unittest20(self):
        ip = self.net["zebra_vip"].usable[2]
        zebra2_ip = self.net["zebra_vip"].usable[1]
        zebra3_ip = self.net["zebra_vip"].usable[6]
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        self.searchoutput(out,
                          r"Service Address: hostname$"
                          r"\s+Address: unittest20\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % ip,
                          command)
        self.searchoutput(out,
                          r"Service Address: zebra2$"
                          r"\s+Address: zebra2\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra2_ip,
                          command)
        self.searchoutput(out,
                          r"Service Address: zebra3$"
                          r"\s+Comments: New service address comments$"
                          r"\s+Address: zebra3\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra3_ip,
                          command)

    def test_111_verify_zebra3_dns(self):
        command = ["show", "fqdn", "--fqdn", "zebra3.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def test_115_reset_zebra3(self):
        new_ip = self.net["zebra_vip"].usable[0]
        self.dsdb_expect_update("zebra3.aqd-unittest.ms.com", ip=new_ip)
        self.noouttest(["update_service_address",
                        "--hostname", "unittest20.aqd-unittest.ms.com",
                        "--name", "zebra3", "--ip", new_ip,
                        "--map_to_primary"])
        self.dsdb_verify()

    def test_116_verify_zebra3_dns(self):
        command = ["show", "fqdn", "--fqdn", "zebra3.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Reverse PTR: unittest20.aqd-unittest.ms.com",
                         command)

    def test_200_bad_interface(self):
        command = ["update_service_address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--name", "hostname", "--interfaces", "eth3"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine unittest20.aqd-unittest.ms.com does not "
                         "have an interface named eth3.", command)

    def test_200_no_interface(self):
        command = ["update_service_address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--name", "hostname", "--interfaces", " ,"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The interface list cannot be empty.", command)


    def test_300_update_ext_service_address(self):
        # check that updating external service addresses do not invoke DSDB
        command = ["update_service_address", "--ip", "192.168.5.26",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth2", "--name", "et-unittest20",
                   "--network_environment", "excx"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
