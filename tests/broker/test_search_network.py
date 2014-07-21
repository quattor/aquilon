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
"""Module for testing the search network command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestSearchNetwork(TestBrokerCommand):

    def testname(self):
        command = ["search_network", "--network=%s" % self.net["tor_net_0"].name]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["tor_net_0"]), command)

    def testip0(self):
        command = ["search_network", "--ip=%s" % self.net["tor_net_0"].ip]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["tor_net_0"]), command)

    def testipcontains(self):
        command = ["search_network", "--ip=%s" % self.net["tor_net_0"].usable[0]]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["tor_net_0"]), command)

    def testtype(self):
        command = ["search_network", "--type=tor_net"]
        out = self.commandtest(command)
        for net in self.net:
            if net.nettype == "tor_net":
                self.matchoutput(out, str(net), command)
            else:
                self.matchclean(out, str(net), command)

    def testphysicalmachine(self):
        # unittest15.aqd-unittest.ms.com
        command = ["search_network", "--machine=ut8s02p1"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["tor_net_0"]), command)

    # The test for virtual machines (with port groups) lives in
    # test_add_10gig_hardware.

    def testfailphysicalmachine(self):
        """This physical machine has no interface."""
        command = ["search_network", "--machine=ut3c1n9"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine ut3c1n9 has no interfaces with a port group "
                         "or assigned to a network.",
                         command)

    # Failure for a virtual machine with no interface is in
    # test_add_10gig_hardware

    def testclusterpg(self):
        command = ["search_network", "--cluster=utecl5", "--pg=user-v710"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["ut01ga2s01_v710"]), command)

    def testcluster(self):
        command = ["search_network", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["verari_eth0"]), command)

    def testfqdn(self):
        command = ["search_network", "--fqdn=unittest15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, str(self.net["tor_net_0"]), command)

    def testlocation(self):
        command = ["search_network", "--building=ut"]
        out = self.commandtest(command)
        for net in self.net:
            if not net.autocreate:
                continue
            if ((net.loc_type == "building" and
                 net.loc_name == "ut") or
                (net.loc_type == "bunker" and
                 net.loc_name == "bucket2.ut")):
                self.matchoutput(out, str(net), command)
            else:
                self.matchclean(out, str(net.ip), command)

    def testexactlocation(self):
        command = ["search_network", "--building=ut", "--exact_location"]
        out = self.commandtest(command)
        for net in self.net:
            if not net.autocreate:
                continue
            if net.loc_type == "building" and net.loc_name == "ut":
                self.matchoutput(out, str(net), command)
            else:
                self.matchclean(out, str(net.ip), command)

    def testfullinfo(self):
        net = self.net["tor_net_0"]
        command = ["search_network", "--ip=%s" % net.ip, "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: %s" % net.name, command)
        self.matchoutput(out, "IP: %s" % net.ip, command)

    def testnoenv(self):
        # Same IP defined differently in different environments
        net = self.net["unknown0"]
        command = ["search", "network", "--ip", net.ip, "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: %s" % net.name, command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchclean(out, "Network Environment: excx", command)
        self.matchclean(out, "Network Environment: utcolo", command)
        self.matchoutput(out, "Netmask: %s" % net.netmask, command)
        self.matchclean(out, "excx-net", command)

    def testwithenv(self):
        # Same IP defined differently in different environments
        net = self.net["unknown0"]
        subnet = net.subnet()[0]
        command = ["search", "network", "--ip", net.ip,
                   "--network_environment", "excx", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: excx-net", command)
        self.matchclean(out, "Network: %s" % net.name, command)
        self.matchoutput(out, "Network Environment: excx", command)
        self.matchclean(out, "Network Environment: internal", command)
        self.matchclean(out, "Network Environment: utcolo", command)
        self.matchoutput(out, "Netmask: %s" % subnet.netmask, command)
        self.matchclean(out, "Netmask: %s" % net.netmask, command)

    def testdynrange(self):
        command = ["search", "network", "--has_dynamic_ranges"]
        out = self.commandtest(command)
        expect = [self.net["dyndhcp0"], self.net["dyndhcp1"],
                  self.net["dyndhcp3"]]
        for net in self.net:
            if not net.autocreate:
                continue
            if net in expect:
                self.matchoutput(out, str(net), command)
            else:
                self.matchclean(out, str(net), command)

    def testdynrangecsv(self):
        command = ["search_network", "--has_dynamic_ranges", "--format", "csv"]
        out = self.commandtest(command)
        expect = [self.net["dyndhcp0"], self.net["dyndhcp1"],
                  self.net["dyndhcp3"]]
        for network in self.net:
            if not network.autocreate:
                continue
            if network in expect:
                self.matchoutput(out, "%s,%s,%s,ut.ny.na,us,a,%s,\n" % (
                    network.name, network.ip, network.netmask, network.nettype),
                    command)
            else:
                self.matchclean(out, str(network.ip), command)

    def testside(self):
        command = ["search", "network", "--side", "b"]
        out = self.commandtest(command)
        self.matchoutput(out, "172.31.64.64/26", command)
        self.matchoutput(out, "172.31.88.0/26", command)
        self.matchclean(out, str(self.net["dyndhcp0"].ip), command)
        self.matchclean(out, str(self.net["unknown0"].ip), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
