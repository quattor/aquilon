#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2012,2013,2014  Contributor
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
"""Module for testing the search network device command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestSearchNetworkDevice(TestBrokerCommand):

    def testwithinterfacecsv(self):
        command = ["search_network_device", "--network_device=ut3gd1r06.aqd-unittest.ms.com",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.net["ut_net_mgmt"].usable[4]
        self.matchoutput(out,
                         "ut3gd1r06.aqd-unittest.ms.com,%s,tor,ut3,ut,"
                         "generic,temp_switch,,xge49,%s" % (ip, ip.mac),
                         command)

    def testwithoutinterfacecsv(self):
        command = ["search_network_device", "--network_device=ut3gd1r01.aqd-unittest.ms.com",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.net["tor_net_12"].usable[0]
        self.matchoutput(out,
                         "ut3gd1r01.aqd-unittest.ms.com,%s,bor,ut3,ut,"
                         "hp,uttorswitch,SNgd1r01,," % ip,
                         command)

    def testbuilding(self):
        command = ["search_network_device", "--building=ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r06.aqd-unittest.ms.com", command)
        self.matchoutput(out, "switchinbuilding.aqd-unittest.ms.com", command)

    def testbuildingexact(self):
        command = ["search_network_device", "--building=ut", "--exact_location"]
        out = self.commandtest(command)
        self.matchoutput(out, "switchinbuilding.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r05", command)
        self.matchclean(out, "ut3gd1r06", command)

    def testcityexact(self):
        command = ["search_network_device", "--city=ny", "--exact_location"]
        self.noouttest(command)

    def testrack(self):
        command = ["search_network_device", "--rack=ut4"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testmodel(self):
        command = ["search_network_device", "--model=uttorswitch"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testvendor(self):
        command = ["search_network_device", "--vendor=hp"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testtype(self):
        command = ["search_network_device", "--type=bor"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testserial(self):
        command = ["search_network_device", "--serial=SNgd1r05_new"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r04.aqd-unittest.ms.com", command)

    def testserialandfullinfo(self):
        command = ["search_network_device", "--serial=SNgd1r05_new", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r05", command)
        self.matchclean(out, "ut3gd1r04", command)

    def testfullinfocsv(self):
        command = ["search_network_device", "--serial=SNgd1r05_new", "--fullinfo",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.net["ut_net_mgmt"].usable[0]
        self.matchoutput(out,
                         "ut3gd1r05.aqd-unittest.ms.com,%s,tor,ut4,ut,"
                         "hp,uttorswitch,SNgd1r05_new,," % ip,
                         command)

    def testsearchswitchall(self):
        command = ["search_network_device", "--all", "--fullinfo"]
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

    def testsearchswitchswitch(self):
        command = ["search_network_device", "--network_device=ut3gd1r04.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net["verari_eth1"].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testsearchswitchallcsv(self):
        command = ["search_network_device", "--all", "--format=csv"]
        out = self.commandtest(command)
        ip = self.net["ut_net_mgmt"].usable[4]
        self.matchoutput(out,
                         "ut3gd1r06.aqd-unittest.ms.com,%s,tor,ut3,ut,"
                         "generic,temp_switch,,xge49,%s" % (ip, ip.mac),
                         command)
        ip = self.net["tor_net_12"].usable[0]
        self.matchoutput(out,
                         "ut3gd1r01.aqd-unittest.ms.com,%s,bor,ut3,ut,"
                         "hp,uttorswitch,SNgd1r01,," % ip,
                         command)

    def testsearchswitchip(self):
        ip = self.net["tor_net_0"].usable[0]
        command = ["search_network_device", "--ip=%s" % ip]
        out = self.commandtest(command)
        self.matchoutput(out, "ut01ga1s02.aqd-unittest.ms.com", command)

    def testsearchswitchipfullinfo(self):
        ip = self.net["tor_net_0"].usable[0]
        command = ["search_network_device", "--ip=%s" % ip, "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut01ga1s02", command)
        self.matchoutput(out,
                         "Primary Name: ut01ga1s02.aqd-unittest.ms.com"
                         " [%s]" % ip, command)
        self.matchoutput(out, "Switch Type: tor", command)
        out = self.commandtest(command)

    def testsearchswitchipcsv(self):
        ip = self.net["tor_net_0"].usable[0]
        command = ["search_network_device", "--ip=%s" % ip, "--format=csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut01ga1s02.aqd-unittest.ms.com,%s,tor,ut8"
                         ",ut,bnt,rs g8000,,xge49,%s" % (ip, ip.mac),
                         command)

    def testsearchvlan(self):
        command = ["search_network_device", "--vlan", "701"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut01ga2s01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut01ga2s02.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut01ga2s03.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut01ga2s04.aqd-unittest.ms.com", command)

        # No such VLAN on these
        self.matchclean(out, "utpgsw0.aqd-unittest.ms.com", command)
        self.matchclean(out, "utpgsw1.aqd-unittest.ms.com", command)

        # Not a ToR switch
        self.matchclean(out, "ut3gd1r01.aqd-unittest.ms.com", command)

        # No VLAN polling was done
        self.matchclean(out, "np01ga2s05.one-nyp.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
