#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015  Contributor
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
"""Module for testing the add network device command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestAddVirtualSwitch(TestBrokerCommand):
    def test_100_add_utvswitch(self):
        self.check_plenary_gone("virtualswitchdata", "utvswitch")
        command = ["add_virtual_switch", "--virtual_switch", "utvswitch"]
        self.noouttest(command)
        self.check_plenary_exists("virtualswitchdata", "utvswitch")

    def test_105_cat_utvswitch(self):
        command = ["cat", "--virtual_switch", "utvswitch", "--data"]
        out = self.commandtest(command)
        self.matchclean(out, "system/virtual_switch/port_groups", command)

    def test_110_bind_portgroup(self):
        net = self.net["autopg1"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch",
                   "--networkip", net.ip, "--type", "user", "--tag", "710"]
        self.noouttest(command)

    def test_111_bind_unregistered_tag(self):
        # Make sure the VLAN number is not registered
        self.noouttest(["show_vlan", "--vlan", "800"])

        net = self.net["vmotion_net"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch",
                   "--networkip", net.ip, "--type", "vmotion", "--tag", "800"]
        self.noouttest(command)

    def test_115_show_utvswitch(self):
        net1 = self.net["autopg1"]
        net2 = self.net["vmotion_net"]
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Virtual Switch: utvswitch
              Port Group: user-v710
                Network: %s
              Port Group: vmotion-v800
                Network: %s
            """ % (net1.ip, net2.ip), command)

    def test_115_show_utvswitch_proto(self):
        nets = {
            self.net["autopg1"]: ("user", 710),
            self.net["vmotion_net"]: ("vmotion", 800),
        }

        command = ["show_virtual_switch", "--virtual_switch", "utvswitch",
                   "--format", "proto"]
        vswitch = self.protobuftest(command, expect=1)[0]
        self.assertEqual(vswitch.name, "utvswitch")
        self.assertEqual(len(vswitch.portgroups), 2)
        pgs = {pg.ip: pg for pg in vswitch.portgroups}
        for net, (usage, network_tag) in nets.items():
            self.assertIn(str(net.ip), pgs)
            self.assertEqual(pgs[str(net.ip)].cidr, net.prefixlen)
            self.assertEqual(pgs[str(net.ip)].usage, usage)
            self.assertEqual(pgs[str(net.ip)].network_tag, network_tag)

    def test_115_cat_utvswitch(self):
        net = self.net["autopg1"]
        command = ["cat", "--virtual_switch", "utvswitch", "--data"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"system/virtual_switch/port_groups/{user-v710}" = nlist\(\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_ip", "%s",\s*'
                          r'"network_tag", 710,\s*'
                          r'"network_type", "%s",\s*'
                          r'"usage", "user"\s*\);' %
                          (net.netmask, net.ip, net.nettype),
                          command)

    def test_120_add_utvswitch2(self):
        self.noouttest(["add_virtual_switch", "--virtual_switc", "utvswitch2",
                        "--comments", "Some virtual switch comments"])

    def test_125_verify_utvswitch2(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Virtual Switch: utvswitch2", command)
        self.matchoutput(out, "Comments: Some virtual switch comments", command)
        self.matchclean(out, "Port Group", command)

    def test_125_verify_all(self):
        command = ["show_virtual_switch", "--all"]
        out = self.commandtest(command)
        self.searchoutput(out, "^utvswitch$", command)
        self.searchoutput(out, "^utvswitch2$", command)

    def test_125_verify_all_proto(self):
        command = ["show_virtual_switch", "--all", "--format", "proto"]
        vswitches = self.protobuftest(command)
        vswitch_names = set(msg.name for msg in vswitches)
        for vswitch_name in ("utvswitch", "utvswitch2"):
            self.assertIn(vswitch_name, vswitch_names)

    def test_130_add_camelcase(self):
        self.noouttest(["add_virtual_switch", "--virtual_switch", "CaMeLcAsE"])
        self.check_plenary_exists("virtualswitchdata", "camelcase")
        self.check_plenary_gone("virtualswitchdata", "CaMeLcAsE")

    def test_140_bind_autopg2(self):
        net = self.net["autopg2"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch2",
                   "--networkip", net.ip, "--type", "user", "--tag", "710"]
        self.noouttest(command)

    def test_200_add_utvswitch_again(self):
        command = ["add_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Virtual Switch utvswitch already exists.",
                         command)

    def test_200_bad_name(self):
        command = ["add_virtual_switch", "--virtual_switch", "oops@!"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'oops@!' is not a valid value for --virtual_switch.",
                         command)

    def test_200_bind_again(self):
        net = self.net["autopg1"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch",
                   "--networkip", net.ip, "--type", "user", "--tag", "710"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Port Group user-v710 is already bound to "
                         "virtual switch utvswitch.", command)

    def test_200_bind_different_type(self):
        net = self.net["autopg1"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch2",
                   "--networkip", net.ip, "--type", "storage", "--tag", "710"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Port Group user-v710 is already used as "
                         "type user.", command)

    def test_200_bind_different_tag(self):
        net = self.net["autopg1"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch2",
                   "--networkip", net.ip, "--type", "user", "--tag", "711"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Port Group user-v710 is already tagged as 710.",
                         command)

    def test_200_bind_duplicate_tag(self):
        net = self.net["ut14_net"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch",
                   "--networkip", net.ip, "--type", "user", "--tag", "710"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Virtual Switch utvswitch already has a port group "
                         "with tag 710.",
                         command)

    def test_200_bind_bad_type(self):
        net = self.net["autopg1"]
        command = ["bind_port_group", "--virtual_switch", "utvswitch2",
                   "--networkip", net.ip, "--type", "vcs", "--tag", "710"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown VLAN type 'vcs'. Valid values are: ",
                         command)

    def test_300_update_utvswitch2(self):
        self.noouttest(["update_virtual_switch",
                        "--virtual_switch", "utvswitch2",
                        "--comments", "New vswitch comments"])

    def test_305_verify_update_utvswitch2(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Virtual Switch: utvswitch2", command)
        self.matchoutput(out, "Comments: New vswitch comments", command)

    def test_310_clear_comments(self):
        self.noouttest(["update_virtual_switch",
                        "--virtual_switch", "utvswitch2", "--comments", ""])

    def test_315_verify_clear_comments(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch2"]
        out = self.commandtest(command)
        self.matchclean(out, "Comments", command)

    def test_320_search_net_by_pg(self):
        net1 = self.net["autopg1"]
        net2 = self.net["vmotion_net"]
        command = ["search_network", "--pg", "vmotion-v800"]
        out = self.commandtest(command)
        self.matchoutput(out, str(net2.ip), command)
        self.matchclean(out, str(net1.ip), command)

    def test_320_search_net_by_usage(self):
        net1 = self.net["autopg1"]
        net2 = self.net["vmotion_net"]
        command = ["search_network", "--pg", "vmotion"]
        out = self.commandtest(command)
        self.matchoutput(out, str(net2.ip), command)
        self.matchclean(out, str(net1.ip), command)

    def test_400_unbind_nonregistered(self):
        net = self.net["unknown0"]
        command = ["unbind_port_group", "--virtual_switch", "utvswitch",
                   "--networkip", net.ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Network unknown0 [%s/%d] is not assigned to a "
                         "port group." % (net.ip, net.prefixlen), command)

    def test_400_unbind_bad_vswitch(self):
        net = self.net["vmotion_net"]
        command = ["unbind_port_group", "--virtual_switch", "utvswitch2",
                   "--networkip", net.ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Port Group vmotion-v800 is not bound to "
                         "virtual switch utvswitch2.", command)

    def test_400_unbind_bad_tag(self):
        command = ["unbind_port_group", "--virtual_switch", "utvswitch", "--tag", 900]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Virtual Switch utvswitch does not have a port "
                         "group tagged with 900.", command)

    def test_800_unregister_pg(self):
        net = self.net["vmotion_net"]
        self.noouttest(["unbind_port_group", "--virtual_switch", "utvswitch",
                        "--networkip", net.ip])

    def test_805_verify_unregister(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.commandtest(command)
        self.matchclean(out, "vmotion", command)

    def test_805_verify_pg_cleanup(self):
        # The PortGroup object should be gone when the last reference is deleted
        self.noouttest(["search_network", "--pg", "vmotion-v800"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVirtualSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
