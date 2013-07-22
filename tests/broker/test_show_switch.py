#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Module for testing the show switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowSwitch(TestBrokerCommand):

    def testshowswitchall(self):
        command = ["show_switch", "--all"]
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
        command = ["show_switch", "--switch=ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net["verari_eth1"].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testshowswitchallcsv(self):
        # Verify both with and without an interface
        command = ["show_switch", "--all", "--format=csv"]

    def testshowswitchswitchcsv(self):
        command = ["show_switch", "--switch=ut3gd1r04.aqd-unittest.ms.com",
                   "--format=csv"]


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
