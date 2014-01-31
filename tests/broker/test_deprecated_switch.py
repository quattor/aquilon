#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Module for testing deprecated switch commands."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDeprecatedSwitch(TestBrokerCommand):

    def setUp(self, *args, **kwargs):
        super(TestDeprecatedSwitch, self).setUp(*args, **kwargs)
        self.fqdn_pri = 'ut3gd1r03.aqd-unittest.ms.com'
        self.ip_pri = self.net["tor_net_12"].usable[3]
        self.fqdn_vlan = 'ut3gd1r03-vlan980.aqd-unittest.ms.com'
        self.ip_vlan = self.net["tor_net_12"].usable[4]

    def test_100_add_switch(self):
        self.dsdb_expect_add(self.fqdn_pri, self.ip_pri, "xge48")
        command = ["add", "switch",
                   "--type", "tor",
                   "--switch", self.fqdn_pri,
                   "--interface", "xge48",
                   "--ip", self.ip_pri,
                   "--rack", "ut3",
                   "--model", "uttorswitch"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Command add_switch is deprecated.", command)
        self.dsdb_verify()

    def test_110_add_interface(self):
        command = ["add", "interface", "--interface", "vlan980",
                   "--switch", self.fqdn_pri]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "The --switch option is deprecated.", command)

    def test_120_add_interface_address(self):
        self.dsdb_expect_add(self.fqdn_vlan, self.ip_vlan,
                             "vlan980", primary=self.fqdn_pri)
        command = ["add", "interface", "address",
                   "--switch", self.fqdn_pri,
                   "--interface", "vlan980", "--ip", self.ip_vlan]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "The --switch option is deprecated.", command)
        self.dsdb_verify()

    def test_200_update_switch(self):
        self.dsdb_expect_update(self.fqdn_pri, comments="LANWAN")
        self.dsdb_expect_update(self.fqdn_vlan, iface='vlan980', comments="LANWAN")
        command = ["update", "switch",
                   "--switch", self.fqdn_pri,
                   "--comments", "LANWAN"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Command update_switch is deprecated.", command)
        self.dsdb_verify()

    def test_210_update_interface(self):
        self.dsdb_expect_update(self.fqdn_pri, "xge48", mac=self.ip_pri.mac)
        command = ["update_interface", "--interface", "xge48",
                   "--mac", self.ip_pri.mac, "--switch", self.fqdn_pri]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "The --switch option is deprecated.", command)
        self.dsdb_verify()

    def test_300_show_switch(self):
        command = ["show_switch", "--switch", self.fqdn_pri]
        (out, err) = self.successtest(command)
        #self.matchoutput(err, "Command show_switch is deprecated.", command)
        self.matchoutput(out, "Switch: ut3gd1r03", command)
        self.matchoutput(out, "Primary Name: %s [%s]" %
                              (self.fqdn_pri, self.ip_pri), command)
        self.matchoutput(out, "Switch Type: tor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "  Interface: vlan980 (no MAC addr)", command)
        self.matchoutput(out, "    Provides: %s [%s]" %
                              (self.fqdn_vlan, self.ip_vlan), command)
        self.matchoutput(out, "  Interface: xge48 %s" %
                              self.ip_pri.mac, command)
        self.matchoutput(out, "    Provides: %s [%s]" %
                              (self.fqdn_pri, self.ip_pri), command)
        self.matchoutput(out, "  Comments: LANWAN", command)

    def test_400_search_switch(self):
        command = ["search_switch", "--ip", self.ip_pri]
        (out, err) = self.successtest(command)
        #self.matchoutput(err, "Command show_switch is deprecated.", command)
        self.matchoutput(out, self.fqdn_pri, command)

    def test_500_cat(self):
        command = ["cat", "--switch", self.fqdn_pri]
        (out, err) = self.successtest(command)
        #self.matchoutput(err, "Command show_switch is deprecated.", command)
        self.matchoutput(out, "structure template switchdata/%s;" %
                              self.fqdn_pri, command)

    def test_600_del_interface_address(self):
        self.dsdb_expect_delete(self.ip_vlan)
        command = ["del", "interface", "address",
                   "--switch", self.fqdn_pri,
                   "--interface", "vlan980", "--ip", self.ip_vlan]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "The --switch option is deprecated.", command)
        self.dsdb_verify()

    def test_610_del_interface(self):
        command = ["del", "interface", "--interface", "vlan980",
                   "--switch", self.fqdn_pri]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "The --switch option is deprecated.", command)

    def test_620_del_switch(self):
        self.dsdb_expect_delete(self.ip_pri)
        command = ["del", "switch",
                   "--switch", self.fqdn_pri]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Command del_switch is deprecated.", command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeprecatedSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
