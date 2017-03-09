#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

    def test_140_del_extnetwork(self):
        command = ["del_network", "--ip", "192.168.5.0",
                   "--network_environment", "excx"]
        self.noouttest(command)

    def test_200_delnetwork(self):
        for network in self.net:
            if not network.autocreate:
                continue
            command = ["del_network", "--ip=%s" % network.ip]
            self.noouttest(command)

    def test_220_delnetworkdup(self):
        ip = "192.168.10.0"
        self.noouttest(["del", "network", "--ip", ip])

    def test_240_shownetworkall(self):
        for network in self.net:
            if not network.autocreate:
                continue
            command = "show network --ip %s --hosts" % network.ip
            self.notfoundtest(command.split(" "))

    def test_230_searchnetwork(self):
        command = "search network --building ut"
        out = self.noouttest(command.split(" "))

    def test_250_searchnetworkproto(self):
        command = "search network --building ut --format proto"
        self.protobuftest(command.split(" "), expect=0)

    def test_210_delnetworkcards(self):
        command = ["del_network", "--ip=192.168.1.0"]
        self.noouttest(command)

    def test_100_autherror_100(self):
        self.demote_current_user("operations")

    def test_110_autherror_200(self):
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

    def test_120_autherror_300(self):
        command = ["del_network", "--ip", "192.168.3.0",
                   "--network_environment", "cardenv"]
        self.noouttest(command)

    def test_130_autherror_900(self):
        self.promote_current_user()

    def test_160_dellocalnet(self):
        self.noouttest(["del", "network", "--ip", "127.0.0.0"])

    def test_150_delexcx(self):
        net = list(self.net["unknown0"].subnets())[0]
        command = ["del", "network", "--ip", net.ip,
                   "--network_environment", "excx"]
        self.noouttest(command)

    def test_180_delnetsvcmap(self):
        net = self.net["netsvcmap"]
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def test_190_delnetutdmz1(self):
        net = self.net["ut_dmz1"]
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def test_170_delnetperssvcmap(self):
        net = self.net["netperssvcmap"]
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def test_225_delutcolo(self):
        net = self.net["unknown1"]
        command = ["del", "network", "--ip", net.ip,
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def test_260_verifyexcx(self):
        net = list(self.net["unknown0"].subnets())[0]
        command = ["search", "network", "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchclean(out, "excx-net", command)
        self.matchclean(out, str(net.ip), command)

    def test_270_verifynetsvcmap(self):
        net = self.net["netsvcmap"]
        command = ["show", "network", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "netsvcmap", command)
        self.matchclean(out, str(net.ip), command)

    def test_280_verifyutcolo(self):
        net = self.net["unknown1"]
        command = ["search", "network", "--network_environment", "utcolo"]
        out = self.commandtest(command)
        self.matchclean(out, "utcolo-net", command)
        self.matchclean(out, str(net.ip), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
