#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddServiceAddress(TestBrokerCommand):

    def testsystemzebramix(self):
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

    def testaddzebra2(self):
        # Use an address that is smaller than the primary IP to verify that the
        # primary IP is not removed
        ip = self.net["zebra_vip"].usable[1]
        self.dsdb_expect_add("zebra2.aqd-unittest.ms.com", ip, "le1")
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--service_address", "zebra2.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--ip", ip,
                   "--name", "zebra2"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyzebra2(self):
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

    def testverifyzebra2proto(self):
        ip = self.net["zebra_vip"].usable[1]
        command = ["show", "host",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--format", "proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        found = False
        for resource in host.resources:
            if resource.name == "zebra2" and resource.type == "service_address":
                found = True
                self.failUnlessEqual(resource.service_address.ip, str(ip))
                self.failUnlessEqual(resource.service_address.fqdn,
                                     "zebra2.aqd-unittest.ms.com")
                ifaces = ",".join(sorted(resource.service_address.interfaces))
                self.failUnlessEqual(ifaces, "eth0,eth1")
        self.assertTrue(found,
                        "Service address zebra2 not found in the resources. "
                        "Existing resources: %s" %
                        ", ".join(["%s %s" % (res.type, res.name) for res in
                                              host.resources]))

    def testverifyzebra2dns(self):
        ip = self.net["zebra_vip"].usable[1]
        command = ["show", "fqdn", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def testaddzebra3(self):
        # Adding an even lower IP should cause zebra2 to be renumbered in DSDB
        zebra2_ip = self.net["zebra_vip"].usable[1]
        zebra3_ip = self.net["zebra_vip"].usable[0]
        self.dsdb_expect_rename("zebra2.aqd-unittest.ms.com", iface="le1",
                                new_iface="le2")
        self.dsdb_expect_add("zebra3.aqd-unittest.ms.com", zebra3_ip, "le1")
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--service_address", "zebra3.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--ip", zebra3_ip,
                   "--name", "zebra3", "--map_to_primary"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyunittest20(self):
        ip = self.net["zebra_vip"].usable[2]
        zebra2_ip = self.net["zebra_vip"].usable[1]
        zebra3_ip = self.net["zebra_vip"].usable[0]
        command = ["show", "host", "--hostname",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Provides: zebra2.aqd-unittest.ms.com [%s] "
                         "(label: zebra2, service_holder: host)" % zebra2_ip,
                         command)
        self.matchoutput(out,
                         "Provides: zebra3.aqd-unittest.ms.com [%s] "
                         "(label: zebra3, service_holder: host)" % zebra3_ip,
                         command)
        self.matchclean(out, "Auxiliary: zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "Auxiliary: zebra3.aqd-unittest.ms.com", command)

        self.searchoutput(out,
                          r"Service Address: hostname$"
                          r"\s+Bound to: Host unittest20\.aqd-unittest\.ms\.com$"
                          r"\s+Address: unittest20\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % ip,
                          command)
        self.searchoutput(out,
                          r"Service Address: zebra2$"
                          r"\s+Bound to: Host unittest20\.aqd-unittest\.ms\.com$"
                          r"\s+Address: zebra2\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra2_ip,
                          command)
        self.searchoutput(out,
                          r"Service Address: zebra3$"
                          r"\s+Bound to: Host unittest20\.aqd-unittest\.ms\.com$"
                          r"\s+Address: zebra3\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra3_ip,
                          command)

    def testfailbadname(self):
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

    def testfailbadinterface(self):
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

    def testfailbadnetenv(self):
        net = self.net["unknown0"]
        subnet = net.subnet()[0]
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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
