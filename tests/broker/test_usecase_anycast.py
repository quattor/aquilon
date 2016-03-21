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
"""Module for testing how a logical DB might be configured."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin

anycast = {
    "service": "anycast",
    "instance": "global",
    "servers": ["infra2.aqd-unittest.ms.com", "infra3.aqd-unittest.ms.com"],
    "sa_fqdn": "anycast.aqd-unittest.ms.com",
    "sa_ip": lambda self: self.net["zebra_vip"].usable[57],
    "sa_name": "anycast"
}

class TestUsecaseAnycast(MachineTestMixin, TestBrokerCommand):

    def test_100_add_utinfra2(self):
        eth0_ip = self.net["unknown0"].usable[38]
        eth1_ip = self.net["unknown1"].usable[37]
        ip = self.net["zebra_vip"].usable[7]
        self.create_host("infra2.aqd-unittest.ms.com", ip, "ut3c5n14",
                         model="utrackmount", chassis="ut3c5", slot=14,
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=eth0_ip.mac, eth0_ip=eth0_ip,
                         eth0_fqdn="infra2-e0.aqd-unittest.ms.com",
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="infra2-e1.aqd-unittest.ms.com",
                         zebra=True, personality="utpers-prod")
        command = ["make", "--hostname", "infra2.aqd-unittest.ms.com"]
        self.statustest(command)

    def test_100_add_utinfra3(self):
        eth0_ip = self.net["unknown0"].usable[39]
        eth1_ip = self.net["unknown1"].usable[38]
        ip = self.net["zebra_vip"].usable[8]
        self.create_host("infra3.aqd-unittest.ms.com", ip, "ut3c5n15",
                         model="utrackmount", chassis="ut3c5", slot=15,
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=eth0_ip.mac, eth0_ip=eth0_ip,
                         eth0_fqdn="infra3-e0.aqd-unittest.ms.com",
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="infra3-e1.aqd-unittest.ms.com",
                         zebra=True, personality="utpers-prod")
        command = ["make", "--hostname", "infra3.aqd-unittest.ms.com"]
        self.statustest(command)

    def test_200_add_service(self):
        self.noouttest(["add_service", "--service", anycast['service']])
        self.noouttest(["add_service", "--service", anycast['service'],
                        "--instance", anycast['instance']])

    def test_201_verify_service(self):
        command = ["show_service", "--service", anycast['service']]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service: %s Instance: %s" % (anycast['service'],
                                                       anycast['instance']),
                         command)

    def test_300_add_service_address(self):
        self.dsdb_expect_add(anycast['sa_fqdn'], anycast['sa_ip'](self))
        for server in anycast['servers']:
            command = ["add", "service", "address",
                       "--hostname", server,
                       "--service_address", anycast['sa_fqdn'],
                       "--name", anycast['sa_name'],
                       "--interfaces", "eth0,eth1",
                       "--ip", anycast['sa_ip'](self),
                       "--shared"]
            out = self.statustest(command)
        self.dsdb_verify()

    def test_400_bind_server(self):
        for server in anycast['servers']:
            self.noouttest(["bind", "server",
                            "--hostname", server,
                            "--service_address", anycast['sa_name'],
                            "--service", anycast['service'],
                            "--instance", anycast['instance']])

    def test_401_verify_server(self):
        for server in anycast['servers']:
            command = ["show", "service", "address",
                       "--name", anycast['sa_name'],
                       "--hostname", server]
            out = self.commandtest(command)
            self.matchoutput(out, "Service Address: %s" % anycast['sa_name'],
                             command)
            self.matchoutput(out, "Bound to: Host %s" % server, command)
            self.matchoutput(out, "Address: %s [%s]" % (anycast['sa_fqdn'],
                                                        anycast['sa_ip'](self)),
                             command)
            self.matchoutput(out, "Interfaces: eth0, eth1", command)

    def test_600_unbind_server(self):
        for server in anycast['servers']:
            self.noouttest(["unbind", "server",
                            "--hostname", server,
                            "--service_address", anycast['sa_name'],
                            "--service", anycast['service'],
                            "--instance", anycast['instance']])

    def test_700_del_service_address(self):
        self.dsdb_expect_delete(anycast['sa_ip'](self))
        for server in anycast['servers']:
            command = ["del", "service", "address",
                       "--hostname", server,
                       "--name", anycast['sa_name']]
            out = self.statustest(command)
        self.dsdb_verify()

    def test_701_verify_service_address(self):
        command = ["show_address", "--fqdn", anycast['sa_fqdn']]
        self.notfoundtest(command)

    def test_800_del_service(self):
        self.noouttest(["del_service", "--service", anycast['service'],
                        "--instance", anycast['instance']])
        self.noouttest(["del_service", "--service", anycast['service']])

    def test_900_del_utinfra2(self):
        eth0_ip = self.net["unknown0"].usable[38]
        eth1_ip = self.net["unknown1"].usable[37]
        ip = self.net["zebra_vip"].usable[7]
        self.delete_host("infra2.aqd-unittest.ms.com", ip, "ut3c5n14",
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_900_del_utinfra3(self):
        eth0_ip = self.net["unknown0"].usable[39]
        eth1_ip = self.net["unknown1"].usable[38]
        ip = self.net["zebra_vip"].usable[8]
        self.delete_host("infra3.aqd-unittest.ms.com", ip, "ut3c5n15",
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUsecaseAnycast)
    unittest.TextTestRunner(verbosity=2).run(suite)

