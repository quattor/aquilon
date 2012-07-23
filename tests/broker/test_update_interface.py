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
"""Module for testing the update interface command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateInterface(TestBrokerCommand):

    badhost = "unittest02.one-nyp.ms.com"

    def test_100_update_ut3c5n10_eth0_mac_bad(self):
        # see testaddunittest02
        oldmac = self.net.unknown[0].usable[0].mac
        mac = self.net.unknown[0].usable[11].mac
        self.dsdb_expect_update(self.badhost, "eth0", mac=mac, fail=True,
                                comments="Updated interface comments")
        command = ["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--mac", mac,
                        "--comments", "Updated interface comments"]
        out = self.badrequesttest(command)
        self.dsdb_verify()
        self.matchoutput(out, "DSDB update failed", command)

        out = self.commandtest(["show", "host", "--hostname", self.badhost])
        self.matchoutput(out, "Interface: eth0 %s" % oldmac, command)

    def test_105_update_ut3c5n10_eth0_mac_good(self):
        mac = self.net.unknown[0].usable[11].mac
        self.dsdb_expect_update("unittest02.one-nyp.ms.com", "eth0", mac=mac,
                                comments="Updated interface comments")
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--mac", mac,
                        "--comments", "Updated interface comments"])
        self.dsdb_verify()

    def test_110_update_ut3c5n10_eth0_ip_bad(self):
        oldip = self.net.unknown[0].usable[0]
        newip = self.net.unknown[0].usable[11]
        self.dsdb_expect_update(self.badhost, "eth0", newip, fail=True)
        command = ["update", "machine", "--machine", "ut3c5n10", "--ip", newip]

        out = self.badrequesttest(command)
        self.dsdb_verify()
        self.matchoutput(out, "Could not update machine in DSDB", command)

        out = self.commandtest(["show", "host", "--hostname", self.badhost])
        self.matchoutput(out, "Primary Name: %s [%s]" % (self.badhost, oldip), command)

    def test_115_update_ut3c5n10_eth0_ip_good(self):
        oldip = self.net.unknown[0].usable[0]
        newip = self.net.unknown[0].usable[11]
        self.dsdb_expect_update(self.badhost, "eth0", newip)

        self.noouttest(["update", "machine", "--machine", "ut3c5n10",
                        "--ip", newip])
        self.dsdb_verify()

    def test_120_update_ut3c5n10_eth1(self):
        self.noouttest(["update", "interface", "--interface", "eth1",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--mac", self.net.unknown[0].usable[12].mac,
                        "--boot", "--model", "e1000"])

    def test_120_update_ut3c5n10_eth2(self):
        self.notfoundtest(["update", "interface", "--interface", "eth2",
            "--machine", "ut3c5n10", "--boot"])

    def test_130_update_switch(self):
        mac = self.net.tor_net[8].usable[0].mac
        self.dsdb_expect_update("ut3gd1r06.aqd-unittest.ms.com", "xge49",
                                mac=mac, comments="Some interface comments")
        command = ["update_interface", "--interface=xge49",
                   "--comments=Some interface comments",
                   "--mac", mac, "--switch=ut3gd1r06.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_130_update_chassis(self):
        mac = self.net.unknown[0].usable[24].mac
        self.dsdb_expect_update("ut3c5.aqd-unittest.ms.com", "oa", mac=mac,
                                comments="Chassis interface comments")
        command = ["update", "interface", "--chassis", "ut3c5",
                   "--interface", "oa", "--mac", mac,
                   "--comments", "Chassis interface comments"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_140_fliproute1(self):
        command = ["update", "interface", "--interface", "eth0",
                   "--machine", "unittest25.aqd-unittest.ms.com",
                   "--nodefault_route"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Warning: machine unittest25.aqd-unittest.ms.com "
                         "has no default route, hope that's ok.", command)

    def test_145_fliproute2(self):
        command = ["update", "interface", "--interface", "eth1",
                   "--machine", "unittest25.aqd-unittest.ms.com",
                   "--default_route"]
        self.noouttest(command)

    def test_150_breakbond(self):
        command = ["update", "interface", "--machine", "ut3c5n3",
                   "--interface", "eth1", "--clear_master"]
        self.noouttest(command)
        # Should fail the second time
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Public Interface eth1 of machine "
                         "unittest21.aqd-unittest.ms.com is not a slave.",
                         command)

    def test_160_rename(self):
        command = ["update", "interface", "--switch", "ut3gd1r04",
                   "--interface", "vlan110", "--rename_to", "vlan220"]
        self.dsdb_expect_rename("ut3gd1r04-vlan110.aqd-unittest.ms.com",
                                "ut3gd1r04-vlan220.aqd-unittest.ms.com",
                                "vlan110", "vlan220")
        self.dsdb_expect_rename("ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com",
                                "ut3gd1r04-vlan220-hsrp.aqd-unittest.ms.com",
                                "vlan110_hsrp", "vlan220_hsrp")
        self.noouttest(command)
        self.dsdb_verify()

    def test_200_update_bad_mac(self):
        mac = self.net.tor_net[6].usable[0].mac
        command = ["update", "interface", "--interface", "eth0",
                   "--machine", "ut3c5n10", "--mac", mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use by on-board admin "
                         "interface xge49 of switch "
                         "ut3gd1r04.aqd-unittest.ms.com" % mac,
                         command)

    def test_200_update_bad_host(self):
        # Use host name instead of machine name
        self.notfoundtest(["update", "interface", "--interface", "eth0",
                           "--machine", "unittest02.one-nyp.ms.com"])

    def test_200_update_vlan_model(self):
        command = ["update", "interface", "--machine", "ut3c5n10",
                   "--interface", "eth1.2", "--model", "e1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model/vendor can not be set for a VLAN "
                         "interface", command)

    def test_200_update_bonding_model(self):
        command = ["update", "interface", "--machine", "ut3c5n3",
                   "--interface", "bond0", "--model", "e1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model/vendor can not be set for a bonding "
                         "interface", command)

    def test_200_fail_switch_boot(self):
        command = ["update_interface", "--boot", "--interface=xge49",
                   "--switch=ut3gd1r01.aqd-unittest.ms.com"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "cannot use the --boot option.", command)

    def testi_200_fail_no_interface(self):
        command = ["update_interface", "--interface=xge49",
                   "--comments=This should fail",
                   "--switch=ut3gd1r01.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Interface xge49, switch ut3gd1r01.aqd-unittest.ms.com "
                         "not found",
                         command)

    def test_200_fail_switch_model(self):
        command = ["update", "interface", "--switch", "ut3gd1r01",
                   "--interface", "xge", "--model", "e1000"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "update_interface --switch cannot use the "
                         "--model option.", command)

    def test_200_fail_chassis_model(self):
        command = ["update", "interface", "--chassis", "ut3c5",
                   "--interface", "oa", "--model", "e1000"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "update_interface --chassis cannot use the "
                         "--model option.", command)

    def test_200_not_a_machine(self):
        command = ["update", "interface", "--interface", "xge49",
                   "--machine", "ut3gd1r06.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a machine", command)

    def test_200_not_a_switch(self):
        command = ["update", "interface", "--interface", "eth0",
                   "--switch", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a switch", command)

    def test_200_fail_bad_iface_chassis(self):
        command = ["update", "interface", "--chassis", "ut3c5",
                   "--interface", "eth0", "--comments", "bad-interface"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface eth0, chassis ut3c5.aqd-unittest.ms.com "
                         "not found.", command)

    def test_200_fail_invalid_chassis_option(self):
        command = ["update", "interface", "--chassis", "ut3c5",
                   "--interface", "oa", "--autopg"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "update_interface --chassis cannot use the "
                         "--autopg option.", command)

    def test_200_rename_existing(self):
        command = ["update", "interface", "--machine", "ut3c5n10",
                   "--interface", "eth0", "--rename_to", "eth1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine unittest02.one-nyp.ms.com already has "
                         "an interface named eth1.", command)

    def test_300_verify_show_ut3c5n10_interfaces(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Comments: Updated interface comments", command)
        self.searchoutput(out, r"Interface: eth0 %s$" %
                          self.net.unknown[0].usable[11].mac.lower(), command)
        self.matchoutput(out, "Provides: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[11], command)
        self.searchoutput(out, r"Interface: eth1 %s \[boot, default_route\]" %
                          self.net.unknown[0].usable[12].mac.lower(), command)
        # Verify that the primary name got updated
        self.matchoutput(out, "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[11], command)
        self.matchclean(out, str(self.net.unknown[0].usable[0]), command)

    def test_300_verify_cat_ut3c5n10_interfaces(self):
        #FIX ME: this doesn't really test anything at the moment: needs to be
        #statefully parsing the interface output
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\),'
                          % self.net.unknown[0].usable[11].mac,
                          command)
        self.searchoutput(out,
                          r'"eth1", create\("hardware/nic/intel/e1000",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % self.net.unknown[0].usable[12].mac,
                          command)

    def test_300_verify_cat_unittest02_interfaces(self):
        net = self.net.unknown[0]
        eth0ip = net.usable[11]
        eth1ip = net.usable[12]
        # Use --generate as update_interface does not update the on-disk
        # templates
        command = "cat --hostname unittest02.one-nyp.ms.com --data --generate"
        out = self.commandtest(command.split(" "))
        # After flipping the boot flag, the static route should now appear on
        # eth0
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest02.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "4.2.1.1",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (net.broadcast, net.gateway,
                           eth0ip, net.netmask),
                          command)
        self.searchoutput(out, r'"eth1", nlist\(\s*"bootproto", "none"\s*\)',
                          command)
        self.searchoutput(out,
                          r'"eth1\.2", nlist\(\s*'
                          r'"bootproto", "none",\s*'
                          r'"physdev", "eth1",\s*'
                          r'"vlan", true\s*\)',
                          command)

    def test_300_verify_switch(self):
        command = ["show_switch",
                   "--switch=ut3gd1r06.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r06", command)
        self.matchoutput(out,
                         "Interface: xge49 %s" %
                         self.net.tor_net[8].usable[0].mac,
                         command)
        self.matchoutput(out, "Comments: Some interface comments", command)

    def test_300_verify_cat_fliproute(self):
        command = ["cat", "--hostname", "unittest25.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/network/default_gateway" = "%s";' %
                         self.net.unknown[1][2], command)

    def test_300_verify_show_fliproute(self):
        command = ["show", "host", "--hostname", "unittest25.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Interface: eth0 %s [boot]" %
                         self.net.unknown[0].usable[20].mac, command)
        self.matchoutput(out, "Interface: eth1 %s [default_route]" %
                         self.net.unknown[0].usable[21].mac, command)

    def test_300_verify_chassis(self):
        old_mac = self.net.unknown[0].usable[6].mac
        new_mac = self.net.unknown[0].usable[24].mac
        command = ["show", "chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Interface: oa %s" % new_mac, command)
        self.matchclean(out, old_mac, command)
        self.matchoutput(out, "Comments: Chassis interface comments", command)

    def test_300_verify_rename(self):
        command = ["show", "switch", "--switch", "ut3gd1r04"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"Interface: vlan220 \(no MAC addr\)$"
                          r"\s+Type: oa$"
                          r"\s+Network Environment: internal$"
                          r"\s+Provides: ut3gd1r04-vlan220.aqd-unittest.ms.com \[%s\]$"
                          r"\s+Provides: ut3gd1r04-vlan220-hsrp.aqd-unittest.ms.com \[%s\] \(label: hsrp\)$"
                          % (self.net.tor_net[12].usable[1],
                             self.net.tor_net[12].usable[2]),
                          command)
        self.matchclean(out, "vlan110", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)
