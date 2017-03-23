#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the show network device command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowNetworkDevice(TestBrokerCommand):

    def testshowswitchall(self):
        command = ["show_network_device", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r01.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_12"].usable[0],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)
        self.matchoutput(out, "Serial: SNgd1r01", command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net["ut10_eth1"].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: tor", command)

    def testshowswitchswitch(self):
        command = ["show_network_device", "--network_device=ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net["ut10_eth1"].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testshowswitchproto(self):
        command = ["show_network_device", "--format=proto",
                   "--network_device=ut3gd1r04.aqd-unittest.ms.com"]
        netdev = self.protobuftest(command, expect=1)[0]
        self.assertEqual(netdev.primary_name, "ut3gd1r04.aqd-unittest.ms.com")
        self.assertEqual(netdev.hardware.label, "ut3gd1r04")
        self.assertEqual(netdev.hardware.model.name, "uttorswitch")
        self.assertEqual(netdev.hardware.location.fullname, "ut3")
        self.assertEqual(netdev.hardware.interfaces[0].device, "loop0")

    def testshowswitchallcsv(self):
        command = ["show_network_device", "--all", "--format=csv"]
        out = self.commandtest(command)
        ip = self.net["tor_net_12"].usable[0]
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,SNgd1r01,xge49," % ip,
                         command)

        ip = self.net["ut10_eth1"].usable[1]
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,,loop0," % ip,
                         command)

        ip = self.net["np06bals03_v103"][5]
        self.matchoutput(out, "np06bals03.ms.com,%s,tor,"
                         "np7,np,bnt,rs g8000,,gigabitethernet0/1,00:18:b1:89:86:00" % ip,
                         command)

    def testshowswitchswitchcsv(self):
        command = ["show_network_device", "--network_device=ut3gd1r04.aqd-unittest.ms.com",
                   "--format=csv"]
        out = self.commandtest(command)

        oldip = self.net["ut10_eth1"].usable[0]
        newip = self.net["ut10_eth1"].usable[1]
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,,loop0," % newip,
                         command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,,vlan110," % newip,
                         command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com,%s,bor,"
                         "ut3,ut,hp,uttorswitch,,xge49,%s" % (newip, oldip.mac),
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
