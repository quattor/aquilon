#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2017,2018  Contributor
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
"""Module for testing the show network command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowNetwork(TestBrokerCommand):
    network_details = {
        "service_addresses": {
            "zebra_vip": ["unittest20.aqd-unittest.ms.com", "infra1.aqd-unittest.ms.com", "infra2.aqd-unittest.ms.com",
                            "zebra2.aqd-unittest.ms.com", "zebra3.aqd-unittest.ms.com"],
            "zebra_vip2": ["infra1.one-nyp.ms.com", "infra2.one-nyp.ms.com"]
        },
        "hosts": {"zebra_vip": False, "zebra_vip2": False, "np_bucket2_vip": False, "np_bucket2_localvip": False,
                  "aurora1": False, "aurora2": False, "routing2": False, "autopg1": False, "switch_loopback": False,
                  "switch_sync": False, "routing3": False, "refreshtest3": False, "refreshtest4": False,
                  "refreshtest5": False, "ut_dmz1": False, "dyndhcp0": False, "dyndhcp1": False, "dyndhcp2": False,
                  "dyndhcp3": False, "dyndhcp5": False, "cardnetwork": False, "unknown0": False,
                  "ipv6_test": False, "ut9_chassis": False}
    }

    network_not_exist = ['netuc_transit_2b', 'netuc_transit_2a', 'netuc_transit_4a', 'netuc_transit_4b',
                         'reserved_dont_use_1', 'refreshtest2', 'reserved_dont_use_2', 'reserved_dont_use_3',
                         'refreshtest1', 'netuc_transit_3a', 'netuc_transit_3b', 'refresh_bunker',
                         'netuc_transit_1b', 'netuc_transit_1a', 'netuc_netmgmt_1b', 'netuc_netmgmt_1a']

    def _test_network_detailed_output(self, out, net, command, hosts=False, service_addresses=[]):
        self.matchoutput(out, "Network: {}".format(net.name), command)
        self.matchoutput(out, "IP: {}".format(net.network_address), command)
        self.matchoutput(out, "{}: {}".format(net.loc_type.title(), net.loc_name), command)
        self.matchoutput(out, "Side: {}".format(net.side), command)
        # To Do: netmask not present for ip6 networks
        # self.matchoutput(out, "Netmask: {}".format(net.netmask), command)
        if hosts:
            cmd = ["search_host", "--networkip", net.network_address, "--format=proto"]
            hosts = self.protobuftest(cmd)
            for host in hosts:
                self.matchoutput(out, "{}".format(host.fqdn), command)
        if service_addresses:
            for srv in service_addresses:
                self.matchoutput(out, "{}".format(srv), command)

    def _test_network_detailed_output_protobuf(self, proto_out, net, hosts=False, service_addresses=[]):
        self.assertEqual(net.name, proto_out.name)
        self.assertEqual(str(net.network_address), proto_out.ip)
        # To Do: netmask not present for ip6 networks
        # self.assertEqual(net.netmask, proto_out.netmask)
        self.assertEqual(net.side, proto_out.side)
        self.assertEqual(net.loc_name, proto_out.location.name)

        if hosts:
            cmd = ["search_host", "--networkip", net.network_address, "--format=proto"]
            hosts = self.protobuftest(cmd)
            for host in hosts:
                # Cannot compare the hostnames and fqdn cause search host and show network --hosts
                # Host fqdn and hostname values are set differently
                hw_labels = [x.machine.name for x in proto_out.hosts]
                if host.machine.name:
                    self.assertIn(host.machine.name, hw_labels)
        if service_addresses:
            for srv in service_addresses:
                self.assertIn(srv, [srv.fqdn for srv in proto_out.service_addresses])

    def test_100_show_network_ip(self):
        net = self.net["unknown0"]
        ip = net.network_address
        command = ["show_network", "--ip", ip]
        out = self.commandtest(command)
        self._test_network_detailed_output(out, net, command)

    def test_105_show_network_ip_hosts(self):
        net = self.net["unknown0"]
        ip = net.network_address
        command = ["show_network", "--ip", ip, "--hosts"]
        out = self.commandtest(command)
        self._test_network_detailed_output(out, net, command, hosts=True)

    def test_110_show_network_ip_all_addresses(self):
        net = self.net["zebra_vip"]
        ip = net.network_address
        command = ["show_network", "--ip", ip, "--address_assignments"]
        out = self.commandtest(command)
        self._test_network_detailed_output(out, net, command, hosts=False,
                                           service_addresses=self.network_details["service_addresses"].get("zebra_vip", []))

    def test_111_show_network_ip_all_addresses(self):
        net = self.net["zebra_vip2"]
        ip = net.network_address
        command = ["show_network", "--ip", ip, "--address_assignments", "--hosts"]
        out = self.commandtest(command)
        self._test_network_detailed_output(out, net, command, hosts=False,
                                           service_addresses=self.network_details["service_addresses"].get("zebra_vip2", []))

    def test_115_show_network_all_details(self):
        command = ["show_network", "--all", "--address_assignments"]
        out = self.commandtest(command)
        for net in self.net:
            if net.name in self.network_not_exist:
                continue
            self._test_network_detailed_output(out,
                                               net, command,
                                               hosts=self.network_details["hosts"].get(net.name, True),
                                               service_addresses=self.network_details["service_addresses"].get(net.name,
                                                                                                               []))

    def test_120_show_network_all_details_proto(self):
        command = ["show_network", "--all", "--address_assignments", "--format=proto"]
        networks = self.protobuftest(command)
        network_names = [n.name for n in networks]

        for net in self.net:
            if net.name in self.network_not_exist:
                continue
            self.assertIn(net.name, network_names)

        for network in networks:
            # Not test all networks cause some were modified or not exist in the network.csv
            if network.name in ['localnet', 'cardnetwork', 'unknown0']:
                continue
            self._test_network_detailed_output_protobuf(network, self.net[network.name],
                                                       hosts=self.network_details["hosts"].get(network.name, True),
                                                       service_addresses=self.network_details["service_addresses"].get(network.name,
                                                                                                                       []))