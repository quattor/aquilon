#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the add tor_switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from switchtest import VerifySwitchMixin


class TestAddTorSwitch(TestBrokerCommand, VerifySwitchMixin):

# FIXME: If needed, move these out into separate show_switch/show_fqdn tests...
#   def testverifyaddut3gd1r01csv(self):
#       command = "show tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com --format=csv"
#       out = self.commandtest(command.split(" "))
#       self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com,ut3,ut,hp,uttorswitch,SNgd1r01,,,",
#               command)

#   def testverifyshowfqdntorswitch(self):
#       command = "show fqdn --fqdn ut3gd1r01.aqd-unittest.ms.com"
#       out = self.commandtest(command.split(" "))
#       self.matchoutput(out, "Switch: ut3gd1r01",
#                        command)

    # Testing that add tor_switch does not allow a blade....
    def testrejectut3gd1r03(self):
        command = ["add", "tor_switch",
                   "--tor_switch", "ut3gd1r03.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "hs21-8853l5u"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model hs21-8853l5u, machine_type switch not found.",
                         command)

    def testverifyrejectut3gd1r03(self):
        command = "show tor_switch --tor_switch ut3gd1r03.aqd-unittest.ms.com"
        out = self.notfoundtest(command.split(" "))

    # Test adding a switch with an existing rack using --rackid
    def testaddnp997gd1r04(self):
        # Deprecated
        command = ["add", "tor_switch",
                   "--tor_switch", "np997gd1r04.aqd-unittest.ms.com",
                   "--building", "np", "--rackid", "997",
                   "--rackrow", "zz", "--rackcol", "99",
                   "--model", "rs g8000"]
        (out, err) = self.successtest(command)

    def testverifynp997gd1r04(self):
        self.verifyswitch("np997gd1r04.aqd-unittest.ms.com", "bnt", "rs g8000",
                          "np997", "zz", "99")

    def testverifyaddnp997gd1r04csv(self):
        command = "show tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np997gd1r04.aqd-unittest.ms.com,np997,np,bnt,rs g8000,,,", command)

    # Test adding a switch and creating a new rack
    def testaddnp998gd1r01(self):
        # Deprecated
        command = ["add", "tor_switch",
                   "--tor_switch", "np998gd1r01.aqd-unittest.ms.com",
                   "--building", "np", "--rackid", "998",
                   "--rackrow", "yy", "--rackcol", "88",
                   "--model", "ws-c2960-48tt-l"]
        (out, err) = self.successtest(command)

    def testverifynp998gd1r01(self):
        self.verifyswitch("np998gd1r01.aqd-unittest.ms.com",
                          "cisco", "ws-c2960-48tt-l", "np998", "yy", "88")

    def testverifyaddnp998gd1r01csv(self):
        command = "show tor_switch --tor_switch np998gd1r01.aqd-unittest.ms.com --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np998gd1r01.aqd-unittest.ms.com,np998,np,cisco,ws-c2960-48tt-l,,,", command)

    # Test adding a switch but specifying the rack row in upper case
    def testaddnp998gd1r02(self):
        # Deprecated.
        command = ["add", "tor_switch",
                   "--tor_switch", "np998gd1r02.aqd-unittest.ms.com",
                   "--building", "np", "--rackid", "998",
                   "--rackrow", "YY", "--rackcol", "88",
                   "--model", "ws-c2960-48tt-l"]
        (out, err) = self.successtest(command)

    # Test adding a switch, creating a new rack, and adding an IP.
    def testaddnp999gd1r01(self):
        # Deprecated.
        ip = self.net.tor_net[5].usable[0]
        self.dsdb_expect_add("np999gd1r01.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "np999gd1r01.aqd-unittest.ms.com",
                   "--building", "np", "--rackid", "999",
                   "--rackrow", "zz", "--rackcol", "11",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testverifynp999gd1r01(self):
        self.verifyswitch("np999gd1r01.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "np999", "zz", "11",
                          ip=str(self.net.tor_net[5].usable[0]),
                          mac=self.net.tor_net[5].usable[0].mac,
                          interface="xge49")

    def testverifyaddnp999gd1r01csv(self):
        command = ["show_tor_switch", "--format=csv",
                   "--tor_switch=np999gd1r01.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "np999gd1r01.aqd-unittest.ms.com,np999,np,"
                         "bnt,rs g8000,,xge49,%s,%s" %
                         (self.net.tor_net[5].usable[0].mac,
                          self.net.tor_net[5].usable[0]),
                         command)

    def testverifyshowtorswitchrack(self):
        command = "show tor_switch --rack np999"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Switch: np999gd1r01", command)

#   def testverifyshowtorswitchmodel(self):
#       command = "show tor_switch --model uttorswitch"
#       out = self.commandtest(command.split(" "))
#       self.matchoutput(out, "Switch: ut3gd1r01",
#                        command)

    def testverifyshowtorswitchall(self):
        command = "show tor_switch --all"
        out = self.commandtest(command.split(" "))
#       self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out, "Switch: np997gd1r04", command)
        self.matchoutput(out, "Switch: np998gd1r01", command)
        self.matchoutput(out, "Switch: np999gd1r01", command)

    def testaddnp06bals03(self):
        # Deprecated.
        self.dsdb_expect_add("np06bals03.ms.com", "172.31.64.69",
                             "gigabitethernet0_1", "00:18:b1:89:86:00")
        command = ["add", "tor_switch", "--tor_switch", "np06bals03.ms.com",
                   "--building", "np", "--rackid", "7",
                   "--rackrow", "g", "--rackcol", "1", "--model", "rs g8000",
                   "--interface", "gigabitethernet0/1",
                   "--mac", "0018b1898600", "--ip", "172.31.64.69"]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testverifynp06bals03(self):
        self.verifyswitch("np06bals03.ms.com",
                          "bnt", "rs g8000", "np7", "g", "1",
                          ip="172.31.64.69", mac="00:18:b1:89:86:00",
                          interface="gigabitethernet0/1")

    def testaddnp06fals01(self):
        # Deprecated.
        self.dsdb_expect_add("np06fals01.ms.com", "172.31.88.5", "xge49",
                             "00:1c:f6:99:e5:c1")
        command = ["add", "tor_switch", "--tor_switch", "np06fals01.ms.com",
                   "--building", "np", "--rackid", "7",
                   "--rackrow", "g", "--rackcol", "1",
                   "--model", "ws-c2960-48tt-l", "--interface", "xge49",
                   "--mac", "001cf699e5c1", "--ip", "172.31.88.5"]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testverifynp06fals01(self):
        self.verifyswitch("np06fals01.ms.com",
                          "cisco", "ws-c2960-48tt-l", "np7", "g", "1",
                          ip="172.31.88.5", mac="00:1c:f6:99:e5:c1",
                          interface="xge49")

    def testaddut01ga1s02(self):
        # Deprecated.
        ip = self.net.tor_net[0].usable[0]
        self.dsdb_expect_add("ut01ga1s02.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga1s02.aqd-unittest.ms.com",
                   "--building", "ut", "--rackid", "8",
                   "--rackrow", "g", "--rackcol", "2",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testverifyut01ga1s02(self):
        self.verifyswitch("ut01ga1s02.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut8", "g", "2",
                          ip=str(self.net.tor_net[0].usable[0]),
                          mac=self.net.tor_net[0].usable[0].mac,
                          interface="xge49")

    def testaddut01ga1s03(self):
        # Deprecated.
        ip = self.net.tor_net[1].usable[0]
        self.dsdb_expect_add("ut01ga1s03.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga1s03.aqd-unittest.ms.com",
                   "--room", "utroom2", "--rackid", "9",
                   "--rackrow", "g", "--rackcol", "3",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testverifyut01ga1s03(self):
        self.verifyswitch("ut01ga1s03.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut9", "g", "3",
                          ip=str(self.net.tor_net[1].usable[0]),
                          mac=self.net.tor_net[1].usable[0].mac,
                          interface="xge49")

    def testaddut01ga1s04(self):
        # Deprecated.
        ip = self.net.tor_net[2].usable[0]
        self.dsdb_expect_add("ut01ga1s04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga1s04.aqd-unittest.ms.com",
                   "--building", "ut", "--rackid", "10",
                   "--rackrow", "g", "--rackcol", "4",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testverifyut01ga1s04(self):
        self.verifyswitch("ut01ga1s04.aqd-unittest.ms.com",
                          "bnt", "rs g8000", "ut10", "g", "4",
                          ip=str(self.net.tor_net[2].usable[0]),
                          mac=self.net.tor_net[2].usable[0].mac,
                          interface="xge49")

    def testrejectut01ga1s99mac(self):
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga1s99.aqd-unittest.ms.com",
                   "--building", "ut", "--rackid", "8",
                   "--rackrow", "g", "--rackcol", "2",
                   "--model", "rs g8000",
                   "--interface", "xge49",
                   "--mac", self.net.tor_net[0].usable[0].mac,
                   "--ip", self.net.tor_net[0].usable[-2]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use" %
                         self.net.tor_net[0].usable[0].mac,
                         command)

    def testrejectut01ga1s99ip(self):
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga1s99.aqd-unittest.ms.com",
                   "--building", "ut", "--rackid", "8",
                   "--rackrow", "g", "--rackcol", "2",
                   "--model", "rs g8000",
                   "--interface", "xge49",
                   "--mac", self.net.tor_net[0].usable[-2].mac,
                   "--ip", self.net.tor_net[0].usable[0]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use" %
                         self.net.tor_net[0].usable[0],
                         command)

    def testverifyrejectut01ga1s99(self):
        command = "show tor_switch --tor_switch ut01ga1s99.aqd-unittest.ms.com"
        out = self.notfoundtest(command.split(" "))

    def testaddut01ga2s01(self):
        # Deprecated.
        ip = self.net.tor_net2[2].usable[0]
        self.dsdb_expect_add("ut01ga2s01.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga2s01.aqd-unittest.ms.com",
                   "--building", "ut", "--rackid", "11",
                   "--rackrow", "k", "--rackcol", "1",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga2s02(self):
        # Deprecated.
        ip = self.net.tor_net2[2].usable[1]
        self.dsdb_expect_add("ut01ga2s02.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga2s02.aqd-unittest.ms.com",
                   "--building", "ut", "--rackid", "12",
                   "--rackrow", "k", "--rackcol", "2",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddut01ga2s03(self):
        # Deprecated.
        ip = self.net.tor_net2[3].usable[0]
        self.dsdb_expect_add("ut01ga2s03.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "ut01ga2s03.aqd-unittest.ms.com",
                   "--rack", "ut13",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    def testaddnp01ga2s03(self):
        # Deprecated.
        ip = self.net.tor_net2[4].usable[0]
        self.dsdb_expect_add("np01ga2s03.one-nyp.ms.com", ip, "xge49", ip.mac)
        command = ["add", "tor_switch",
                   "--tor_switch", "np01ga2s03.one-nyp.ms.com",
                   "--rack", "np13",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddTorSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
