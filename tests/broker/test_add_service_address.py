#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the add service address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddServiceAddress(TestBrokerCommand):

    def test_100_systemzebramix(self):
        ip = self.net["unknown0"].usable[3]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--name", "e2",
                   "--service_address", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com." % ip,
                         command)

    def test_200_addzebra2(self):
        # Use an address that is smaller than the primary IP to verify that the
        # primary IP is not removed
        ip = self.net["zebra_vip"].usable[1]
        self.dsdb_expect_add("zebra2.aqd-unittest.ms.com", ip)
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--service_address", "zebra2.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--ip", ip,
                   "--name", "zebra2"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Host unittest20.aqd-unittest.ms.com is missing the "
                         "following required services",
                         command)
        self.dsdb_verify()

    def test_210_verifyzebra2(self):
        ip = self.net["zebra_vip"].usable[1]
        command = ["show", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service Address: zebra2", command)
        self.matchoutput(out, "Bound to: Host unittest20.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Address: zebra2.aqd-unittest.ms.com [%s]" % ip,
                         command)
        self.matchoutput(out, "Interfaces: eth0, eth1", command)

    def test_220_verifyzebra2proto(self):
        ip = self.net["zebra_vip"].usable[1]
        command = ["show", "host",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--format", "proto"]
        host = self.protobuftest(command, expect=1)[0]
        found = False
        for resource in host.resources:
            if resource.name == "zebra2" and resource.type == "service_address":
                found = True
                self.assertEqual(resource.service_address.ip, str(ip))
                self.assertEqual(resource.service_address.fqdn,
                                 "zebra2.aqd-unittest.ms.com")
                ifaces = ",".join(sorted(resource.service_address.interfaces))
                self.assertEqual(ifaces, "eth0,eth1")
        self.assertTrue(found,
                        "Service address zebra2 not found in the resources. "
                        "Existing resources: %s" %
                        ", ".join("%s %s" % (res.type, res.name)
                                  for res in host.resources))

    def test_230_verifyzebra2dns(self):
        command = ["show", "fqdn", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def test_300_addzebra3(self):
        zebra3_ip = self.net["zebra_vip"].usable[0]
        self.dsdb_expect_add("zebra3.aqd-unittest.ms.com", zebra3_ip,
                             comments="Some service address comments")
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--prefix", "zebra",
                   "--interfaces", "eth0,eth1", "--ip", zebra3_ip,
                   "--name", "zebra3", "--map_to_primary",
                   "--comments", "Some service address comments"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Host unittest20.aqd-unittest.ms.com is missing the "
                         "following required services",
                         command)
        self.dsdb_verify()

    def test_310_verifyzebra3dns(self):
        command = ["show", "fqdn", "--fqdn", "zebra3.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Reverse PTR: unittest20.aqd-unittest.ms.com",
                         command)

    def test_320_verifyzebra3audit(self):
        command = ["search_audit", "--keyword", "zebra3.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "[Result: service_address=zebra3.aqd-unittest.ms.com]",
                         command)

    def test_400_verifyunittest20(self):
        ip = self.net["zebra_vip"].usable[2]
        zebra2_ip = self.net["zebra_vip"].usable[1]
        zebra3_ip = self.net["zebra_vip"].usable[0]
        command = ["show", "host", "--hostname",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Provides: zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "Provides: zebra3.aqd-unittest.ms.com", command)
        self.matchclean(out, "Auxiliary: zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "Auxiliary: zebra3.aqd-unittest.ms.com", command)

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
                          r"\s+Comments: Some service address comments$"
                          r"\s+Address: zebra3\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra3_ip,
                          command)

    def test_500_failbadname(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--name", "hostname",
                   "--service_address", "hostname-label.one-nyp.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The hostname service address is reserved for Zebra.  "
                         "Please specify the --zebra_interfaces option when "
                         "calling add_host if you want the primary name of the "
                         "host to be managed by Zebra.",
                         command)

    def test_510_failbadinterface(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth2", "--name", "badiface",
                   "--service_address", "badiface.one-nyp.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine unittest20.aqd-unittest.ms.com does not have "
                         "an interface named eth2.",
                         command)

    def test_520_failbadnetenv(self):
        net = self.net["unknown0"]
        subnet = list(net.subnets())[0]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--name", "badenv",
                   "--service_address", "badenv.one-nyp.ms.com",
                   "--ip", subnet[1], "--network_environment", "excx"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Public Interface eth0 of machine "
                         "unittest20.aqd-unittest.ms.com already has an IP "
                         "address from network environment internal.  Network "
                         "environments cannot be mixed.",
                         command)

    def test_600_addunittest20eth2(self):
        command = ["add_interface", "--machine", "ut3c5n2",
                   "--interface", "eth2", "--mac", "08:00:01:02:20:00"]
        self.successtest(command)

    def test_605_addunittest20eth2addr(self):
        command = ["add_interface_address", "--machine", "ut3c5n2",
                   "--interface", "eth2", "--network_environment", "excx",
                   "--fqdn", "unittest20-e2.aqd-unittest.ms.com",
                   "--ip", "192.168.5.24"]
        self.statustest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

    def test_610_add_extserviceaddress(self):
        # check that adding an external service address does not invoke DSDB
        command = ["add_service_address", "--ip", "192.168.5.25",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth2", "--name", "et-unittest20",
                   "--service_address", "external-unittest20.aqd-unittest.ms.com",
                   "--network_environment", "excx"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Host unittest20.aqd-unittest.ms.com is missing the "
                         "following required services",
                         command)
        # External IP service addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

    def test_620_add_service_address_ipfromtype_vip_setup(self):
        ip = self.net["np_bucket2_vip"].network_address
        command = ["show", "host", "--hostname", "aquilon67.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bunker: bucket2.ut", command)
        command = ["search", "network", "--type", "vip", "--exact_location", "--bunker", "bucket2.ut", "--fullinfo"]
        self.noouttest(command)
        command = ["search", "network", "--type", "vip", "--exact_location", "--bunker", "bucket2.np", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bunker: bucket2.np", command)
        self.matchoutput(out, "IP: {}".format(ip), command)
        self.matchoutput(out, "Network: np_bucket2_vip", command)
        self.matchoutput(out, "Network Type: vip", command)

    def test_625_add_service_address_ipfromtype_vip(self):
        # Test nextip generation for VIP serviceaddreses
        ip = self.net["np_bucket2_vip"].usable[0]
        service_addr = "testaddress.ms.com"
        self.dsdb_expect_add(service_addr, ip)
        command = ["add", "service", "address", "--hostname", "aquilon67.aqd-unittest.ms.com",
                   "--service_address", service_addr, "--name", "test", "--ipfromtype", "vip"]
        self.successtest(command)
        command = ["show", "service", "address", "--name", "test",
                   "--hostname", "aquilon67.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service Address: test", command)
        self.matchoutput(out, "Bound to: Host aquilon67.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Address: testaddress.ms.com [{}]".format(ip),
                         command)
        self.dsdb_verify()

    def test_630_add_service_address_ipfromtype_localvip_setup(self):
        ip1 = self.net["ut_bucket2_localvip"].network_address
        ip2 = self.net["np_bucket2_localvip"].network_address
        command = ["search", "network", "--type", "localvip", "--exact_location", "--bunker", "bucket2.ut", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bunker: bucket2.ut", command)
        self.matchoutput(out, "IP: {}".format(ip1), command)
        self.matchoutput(out, "Network: ut_bucket2_localvip", command)

        command = ["search", "network", "--type", "localvip", "--exact_location", "--bunker", "bucket2.np", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bunker: bucket2.np", command)
        self.matchoutput(out, "IP: {}".format(ip2), command)
        self.matchoutput(out, "Network: np_bucket2_localvip", command)

    def test_635_add_service_address_ipfromtype_localvip(self):
        # Test nextip generation for localvip serviceaddreses
        ip = self.net["ut_bucket2_localvip"].usable[1]
        service_addr = "testlocalvipaddress.ms.com"
        self.dsdb_expect_add(service_addr, ip)
        command = ["add", "service", "address", "--hostname", "aquilon67.aqd-unittest.ms.com",
                   "--service_address", service_addr, "--name", "test2", "--ipfromtype", "localvip"]
        self.successtest(command)
        command = ["show", "service", "address", "--name", "test2",
                   "--hostname", "aquilon67.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service Address: test2", command)
        self.matchoutput(out, "Bound to: Host aquilon67.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Address: testlocalvipaddress.ms.com [{}]".format(ip),
                         command)

    def test_640_add_service_address_ipfromtype_not_bunker(self):
        # Test nextip generation limited to bunkers only
        command = ["add", "service", "address", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--service_address", "dummy.ms.com", "--name", "test3", "--ipfromtype", "localvip"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Host(s) location is not "
                              "inside a Bunker, --ipfromtype cannot be used.", command)

    def test_645_test_del_ipfromtype_test(self):
        ip1 = self.net["np_bucket2_vip"].usable[0]
        ip2 = self.net["ut_bucket2_localvip"].usable[1]
        self.dsdb_expect_delete(ip1)
        command = ["del", "service", "address", "--hostname", "aquilon67.aqd-unittest.ms.com",
                   "--name", "test"]
        self.successtest(command)
        self.dsdb_verify()
        self.dsdb_expect_delete(ip2)
        command = ["del", "service", "address", "--hostname", "aquilon67.aqd-unittest.ms.com",
                   "--name", "test2"]
        self.successtest(command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
