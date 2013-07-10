#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
"""Module for testing the add switch command."""

import unittest
import os
import socket

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

SW_HOSTNAME = "utpgsw0.aqd-unittest.ms.com"


class TestVlan(TestBrokerCommand):

    def getswip(self):
        return self.net.tor_net[10].usable[0]

    def test_001_addvlan714(self):
        command = ["add_vlan", "--vlan=714", "--name=user_714",
                   "--vlan_type=user"]
        self.noouttest(command)

        command = "show vlan --vlan 714"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vlan: 714", command)
        self.matchoutput(out, "Name: user_714", command)

    def test_001_addutpgsw(self):
        ip = self.getswip()

        self.dsdb_expect_add(SW_HOSTNAME, ip, "xge49",
                             ip.mac)
        command = ["add", "switch", "--type", "tor",
                   "--switch", SW_HOSTNAME, "--rack", "ut3",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        self.ignoreoutputtest(command)
        self.dsdb_verify()

    def test_010_pollutpgsw(self):
        command = ["poll", "switch", "--vlan", "--switch",
                   SW_HOSTNAME]
        err = self.statustest(command)

        self.matchoutput(err, "Using jump host nyaqd1.ms.com from service "
                         "instance poll_helper/unittest to run discovery for "
                         "switch utpgsw0.aqd-unittest.ms.com.", command)

        self.matchoutput(err, "vlan 5 is not defined in AQ. Please use "
                "add_vlan to add it.", command)

    # Adding vlan 5 as unknown will suppress poll_switch vlan warning.
    def test_012_addvlan5(self):
        command = ["add_vlan", "--vlan=5", "--name=user_5",
                   "--vlan_type=unknown"]
        self.noouttest(command)

        command = "show vlan --vlan 5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vlan: 5", command)
        self.matchoutput(out, "Name: user_5", command)

    def test_012_pollutpgsw(self):
        command = ["poll", "switch", "--vlan", "--switch",
                   SW_HOSTNAME]
        err = self.statustest(command)

        self.matchoutput(err, "Using jump host nyaqd1.ms.com from service "
                         "instance poll_helper/unittest to run discovery for "
                         "switch utpgsw0.aqd-unittest.ms.com.", command)

        self.matchclean(err, "vlan 5 is not defined in AQ. Please use "
                "add_vlan to add it.", command)

    def test_015_searchswbyvlan(self):
        command = ["search_switch", "--vlan=714",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.getswip()
        self.matchoutput(out,
                         "utpgsw0.aqd-unittest.ms.com,%s,tor,ut3,ut,bnt,"
                         "rs g8000,,xge49,%s" % (ip, ip.mac), command)
        self.matchclean(out,
                         "ut3gd1r01.aqd-unittest.ms.com,4.2.5.8,bor,ut3,ut,hp,"
                         "uttorswitch,SNgd1r01,,", command)

    def test_020_faildelvlan(self):
        command = ["del_vlan", "--vlan=714"]
        errOut = self.badrequesttest(command)
        self.matchoutput(errOut,
                         "VlanInfo 714 is still in use and cannot be "
                         "deleted.", command)

    # Unknown vlans have no dependencies, can be deleted.
    def test_025_delvlan(self):
        command = ["del_vlan", "--vlan=5"]
        self.noouttest(command)

        command = ["show_vlan", "--vlan=5"]
        self.notfoundtest(command)

    def test_030_delutpgsw(self):
        self.dsdb_expect_delete(self.getswip())

        command = "del switch --switch %s" % SW_HOSTNAME
        self.noouttest(command.split(" "))

        plenary = os.path.join(self.config.get("broker", "plenarydir"),
                   "switchdata", "%s.tpl" % SW_HOSTNAME)
        self.failIf(os.path.exists(plenary),
                    "Plenary file '%s' still exists" % plenary)

        self.dsdb_verify()

    def test_040_delvlan(self):
        command = ["del_vlan", "--vlan=714"]
        self.noouttest(command)

        command = ["show_vlan", "--vlan=714"]
        self.notfoundtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVlan)
    unittest.TextTestRunner(verbosity=2).run(suite)
