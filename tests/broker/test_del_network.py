#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del_network command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelNetwork(TestBrokerCommand):

    def testdelnetwork(self):
        for network in self.net:
            if not network.autocreate:
                continue
            command = ["del_network", "--ip=%s" % network.ip]
            self.noouttest(command)

    def testdelauroranetwork(self):
        for ip in ["144.14.174.0", "10.184.155.0"]:
            command = ["del_network", "--ip=%s" % ip]
            self.noouttest(command)

    def testdelnetworkdup(self):
        ip = "192.168.10.0"
        self.noouttest(["del", "network", "--ip", ip])

    def testshownetworkall(self):
        for network in self.net:
            if not network.autocreate:
                continue
            command = "show network --ip %s --hosts" % network.ip
            out = self.notfoundtest(command.split(" "))

    def testshownetwork(self):
        command = "show network --building ut"
        out = self.commandtest(command.split(" "))
        # Unfortunately this command prints a header even if the output is
        # otherwise empty. Check for a dot, as that will match any IP addresses,
        # but not the header.
        self.matchclean(out, ".", command)

    def testshownetworkproto(self):
        command = "show network --building ut --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_netlist_msg(out, expect=0)

    def testdelnetworkcards(self):
        command = ["del_network", "--ip=192.168.1.0"]
        self.noouttest(command)

    def test_autherror_100(self):
        self.demote_current_user("operations")

    def test_autherror_200(self):
        # 192.168.2.0 was never actually created, but that check happens
        # after the auth check.
        command = ["del_network", "--ip", "192.168.2.0"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        allowed_roles = self.config.get("site", "change_default_netenv_roles")
        role_list = allowed_roles.strip().split()
        default_ne = self.config.get("site", "default_network_environment")
        self.matchoutput(out,
                         "Only users with %s can modify networks in the %s "
                         "network environment." % (role_list, default_ne),
                         command)

    def test_autherror_300(self):
        command = ["del_network", "--ip", "192.168.3.0",
                   "--network_environment", "cardenv"]
        self.noouttest(command)

    def test_autherror_900(self):
        self.promote_current_user()

    def testdellocalnet(self):
        self.noouttest(["del", "network", "--ip", "127.0.0.0"])

    def testdelexcx(self):
        net = self.net["unknown0"].subnet()[0]
        command = ["del", "network", "--ip", net.ip,
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testdelnetsvcmap(self):
        net = self.net["netsvcmap"]
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def testdelnetperssvcmap(self):
        net = self.net["netperssvcmap"]
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def testdelutcolo(self):
        net = self.net["unknown1"]
        command = ["del", "network", "--ip", net.ip,
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def testverifyexcx(self):
        net = self.net["unknown0"].subnet()[0]
        command = ["search", "network", "--all", "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchclean(out, "excx-net", command)
        self.matchclean(out, str(net.ip), command)

    def testverifynetsvcmap(self):
        net = self.net["netsvcmap"]
        command = ["search", "network", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "netsvcmap", command)
        self.matchclean(out, str(net.ip), command)

    def testverifyutcolo(self):
        net = self.net["unknown1"]
        command = ["search", "network", "--all", "--network_environment", "utcolo"]
        out = self.commandtest(command)
        self.matchclean(out, "utcolo-net", command)
        self.matchclean(out, str(net.ip), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
