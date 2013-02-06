#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
                         "instance poll_helper/unittest to run CheckNet for "
                         "switch utpgsw0.aqd-unittest.ms.com.", command)

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
