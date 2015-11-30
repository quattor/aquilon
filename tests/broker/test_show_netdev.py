#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2015  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
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
                         self.net["verari_eth1"].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: tor", command)

    def testshowswitchswitch(self):
        command = ["show_network_device", "--network_device=ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net["verari_eth1"].usable[1],
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

    def testshowswitchswitchcsv(self):
        command = ["show_network_device", "--network_device=ut3gd1r04.aqd-unittest.ms.com",
                   "--format=csv"]
        out = self.commandtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
