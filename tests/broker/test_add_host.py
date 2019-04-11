#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
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
"""Module for testing the add host command."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand
from networktest import DummyIP
from machinetest import MachineTestMixin


class TestAddHost(MachineTestMixin, TestBrokerCommand):
    def test_100_add_unittest16_fail_ipfromtype(self):
        # Test fail to use --ipfromtype for hosts not in bunker
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromtype", "localvip", "--ipalgorithm", "lowest",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--archetype", "aquilon",
                   "--personality", "compileserver"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Host location is not "
                              "inside a bunker, --ipfromtype cannot be used.",
                         command)

    def test_101_add_unittest02(self):
        ip = self.net["unknown0"].usable[0]
        # DSDB sync uses the machine comments, not the host comments
        self.dsdb_expect_add("unittest02.one-nyp.ms.com", ip, "eth0", ip.mac,
                             comments="Some machine comments")
        osver = self.config.get("unittest", "linux_version_prev")
        self.noouttest(["add", "host",
                        "--hostname", "unittest02.one-nyp.ms.com", "--ip", ip,
                        "--machine", "ut3c5n10", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", osver,
                        "--personality", "compileserver",
                        "--comments", "Some host comments"])
        self.dsdb_verify()

    def test_105_verify_unittest02(self):
        osver = self.config.get("unittest", "linux_version_prev")
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net["unknown0"].usable[0],
                         command)
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Version: %s" % osver, command)
        self.matchoutput(out, "Advertise Status: False", command)
        self.matchoutput(out, "Host Comments: Some host comments", command)

    def test_105_verify_unittest02_network_osversion(self):
        osver = self.config.get("unittest", "linux_version_prev")
        command = ["show", "network",
                   "--ip", str(self.net["unknown0"].ip),
                   "--format", "proto",
                   "--hosts"]
        network = self.protobuftest(command)[0]
        for i in network.hosts:
            if i.fqdn == 'unittest02.one-nyp.ms.com':
                self.assertEqual(i.operating_system.version, osver)
                break
        else:
            self.fail("Unable to determine osversion")

    def test_105_verify_unittest02_machine(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net["unknown0"].usable[0],
                         command)

    def test_105_verify_unittest02_dns(self):
        command = "search dns --fqdn unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def test_105_verify_unittest02_proto(self):
        command = "show host --hostname unittest02.one-nyp.ms.com --format proto"
        host = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(host.hostname, "unittest02")
        self.assertEqual(host.fqdn, "unittest02.one-nyp.ms.com")
        self.assertEqual(host.dns_domain, "one-nyp.ms.com")
        self.assertEqual(host.machine.name, "ut3c5n10")
        self.assertEqual(host.status, "build")
        self.assertEqual(host.personality.archetype.name, "aquilon")
        self.assertEqual(host.personality.name, "compileserver")
        self.assertEqual(host.personality.host_environment, "dev")
        self.assertEqual(host.domain.name, "unittest")
        self.assertEqual(host.owner_eonid, 3)
        self.assertEqual(len(host.eonid_maps), 0)
        self.assertEqual(host.personality.owner_eonid, 3)
        self.assertEqual(len(host.personality.eonid_maps), 1)
        self.assertEqual(host.personality.eonid_maps[0].target, 'esp')
        self.assertEqual(host.personality.eonid_maps[0].eonid, 3)

    def test_105_cat_fail(self):
        # The plenary should not be there before make/reconfigure was run
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.notfoundtest(command)
        profile = self.build_profile_name("unittest02.one-nyp.ms.com",
                                          domain="unittest")
        self.matchoutput(out, "Plenary file %s not found" % profile, command)

    def test_106_verify_show_host_grns(self):
        command = ["show_host", "--grns",
                   "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest [inherited]", command)
        self.matchoutput(out, "Used by GRN: grn:/ms/ei/aquilon/unittest [target: esp, inherited]", command)

    def test_106_verify_show_host_grns_proto(self):
        command = ["show_host", "--format=proto", "--grns",
                   "--hostname=unittest02.one-nyp.ms.com"]
        host = self.protobuftest(command, expect=1)[0]
        self.assertEqual(host.hostname, "unittest02")
        self.assertEqual(host.dns_domain, "one-nyp.ms.com")
        self.assertEqual(host.fqdn, "unittest02.one-nyp.ms.com")
        self.assertEqual(host.personality.archetype.name, "aquilon")
        self.assertEqual(host.personality.name, "compileserver")
        self.assertEqual(host.personality.host_environment, "dev")
        self.assertEqual(host.status, "build")
        self.assertEqual(host.domain.name, "unittest")
        self.assertEqual(host.owner_eonid, 3)
        self.assertEqual(len(host.eonid_maps), 0)
        self.assertEqual(host.personality.owner_eonid, 3)
        self.assertEqual(len(host.personality.eonid_maps), 1)
        self.assertEqual(host.personality.eonid_maps[0].target, 'esp')
        self.assertEqual(host.personality.eonid_maps[0].eonid, 3)

    def test_110_add_unittest15(self):
        ip = self.net["tor_net_0"].usable[1]
        self.dsdb_expect_add("unittest15.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "host",
                        "--hostname", "unittest15.aqd-unittest.ms.com",
                        "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
                        "--ipalgorithm", "max",
                        "--machine", "ut8s02p1", "--domain", "unittest",
                        "--archetype", "aquilon"])
        self.dsdb_verify()

    def test_115_verify_unittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest15.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_0"].usable[1],
                         command)
        self.matchoutput(out, "Personality: inventory", command)

    def test_120_add_unittest16_bad(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", self.net["dyndhcp1"].usable[-1],
                   "--ipalgorithm", "max",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Failed to find an IP that is suitable for "
                         "--ipalgorithm=max.  Try an other algorithm as there "
                         "are still some free addresses.",
                         command)

    def test_121_add_unittest16_bad_ip(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ip", "not-an-ip-address",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Expected an IP address for --ip: "
                         "u'not-an-ip-address' does not appear to be an IPv4 or IPv6 address.",
                         command)

    def test_122_add_unittest16_bad_domain(self):
        net = self.net["tor_net_0"]
        command = ["add", "host", "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", net.usable[0], "--ipalgorithm", "lowest",
                   "--machine", "ut8s02p2", "--domain", "nomanage",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Adding hosts to domain nomanage "
                         "is not allowed.", command)

    def test_123_add_unittest16_bad_hostname(self):
        net = self.net["tor_net_0"]
        command = ["add", "host", "--hostname", "1unittest16.aqd-unittest.ms.com",
                   "--ipfromip", net.usable[0], "--ipalgorithm", "lowest",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'1unittest16.aqd-unittest.ms.com' is not a valid "
                         "value for hostname.", command)

    def test_124_add_unittest16_good(self):
        net = self.net["tor_net_0"]
        self.dsdb_expect_add("unittest16.aqd-unittest.ms.com", net.usable[2],
                             "eth0", net.usable[2].mac)
        self.noouttest(["add", "host",
                        "--hostname", "unittest16.aqd-unittest.ms.com",
                        "--ipfromip", net.usable[0], "--ipalgorithm", "lowest",
                        "--machine", "ut8s02p2", "--domain", "unittest",
                        "--archetype", "aquilon",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def test_125_verify_unittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest16.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_0"].usable[2],
                         command)
        self.matchoutput(out, "Personality: compileserver", command)

    def test_130_add_unittest17(self):
        ip = self.net["tor_net_0"].usable[3]
        self.dsdb_expect_add("unittest17.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "host",
                        "--hostname", "unittest17.aqd-unittest.ms.com",
                        "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
                        "--machine", "ut8s02p3", "--domain", "unittest",
                        "--archetype", "aquilon"])
        self.dsdb_verify()

    def test_135_verify_unittest17(self):
        # Verifies default os and personality for aquilon
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        osversion = self.config.get("archetype_aquilon", "default_osversion")
        osversion.replace(".", r"\.")
        self.matchoutput(out,
                         "Primary Name: unittest17.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_0"].usable[3],
                         command)
        self.searchoutput(out,
                          r'Operating System: linux\s*'
                          r'Version: %s$' % osversion,
                          command)
        self.matchoutput(out, "Personality: inventory", command)

    def test_140_add_aurora_default_os(self):
        ip = self.net["tor_net_0"].usable[4]
        self.noouttest(["add", "host", "--archetype", "aurora",
                        "--hostname", "test-aurora-default-os.ms.com",
                        "--ip", ip, "--domain", "unittest", "--machine",
                        "ut8s02p4"])

    def test_141_verify_aurora_default_os(self):
        command = "show host --hostname test-aurora-default-os.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: test-aurora-default-os.ms.com", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.searchoutput(out,
                          r'Operating System: linux\s*'
                          r'Version: generic$',
                          command)

    def test_145_add_windows_default_os(self):
        ip = self.net["tor_net_0"].usable[5]
        self.dsdb_expect_add("test-windows-default-os.msad.ms.com", ip,
                             "eth0", self.net["tor_net_0"].usable[5].mac)
        self.noouttest(["add", "host", "--archetype", "windows",
                        "--hostname", "test-windows-default-os.msad.ms.com",
                        "--ip", ip, "--domain", "ut-prod",
                        "--machine", "ut8s02p5"])
        self.dsdb_verify()

    def test_146_verify_windows_default_os(self):
        command = "show host --hostname test-windows-default-os.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: test-windows-default-os.msad.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ut-prod", command)
        self.searchoutput(out,
                          r'Operating System: windows\s*'
                          r'Version: generic$',
                          command)

    def test_150_add_cciss_host(self):
        ip = self.net["unknown0"].usable[18]
        self.dsdb_expect_add("unittest18.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        command = ["add", "host", "--archetype", "aquilon",
                   "--hostname", "unittest18.aqd-unittest.ms.com", "--ip", ip,
                   "--domain", "unittest", "--machine", "ut3c1n8"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_155_add_f5(self):
        # The IP address is also a /32 network
        ip = self.net["f5test"].ip
        self.dsdb_expect_add("f5test.aqd-unittest.ms.com", ip, "eth0",
                             DummyIP(ip).mac)
        command = ["add", "host", "--hostname", "f5test.aqd-unittest.ms.com",
                   "--machine", "f5test", "--ip", ip,
                   "--archetype", "f5", "--domain", "unittest",
                   "--osname", "f5", "--osversion", "generic"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_160_no_default_os(self):
        ip = self.net["vm_storage_net"].usable[25]
        command = ["add", "host", "--archetype", "filer",
                   "--hostname", "filer1.ms.com", "--ip", ip,
                   "--domain", "unittest", "--machine", "filer1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Can not determine a sensible default OS", command)

    def test_165_add_filer(self):
        ip = self.net["vm_storage_net"].usable[25]
        self.dsdb_expect_add("filer1.ms.com", ip, "v0")
        command = ["add", "host", "--archetype", "filer",
                   "--hostname", "filer1.ms.com", "--ip", ip,
                   "--domain", "unittest", "--machine", "filer1",
                   "--osname=ontap", "--osversion=7.3.3p1"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_170_add_cardsmachine(self):
        net = self.net.allocate_network(self, "cards_net", 28, "unknown",
                                        "building", "cards")
        self.create_machine("cardsmachine", "utrackmount", rack="cards1",
                            cpuname="utcpu", cpucount=2, memory=65536,
                            sda_size=600, sda_controller="sas",
                            eth0_mac=net.usable[0].mac)

    def test_171_host_prefix_no_domain(self):
        osver = self.config.get("unittest", "linux_version_curr")
        command = ["add_host", "--machine", "cardsmachine", "--domain", "unittest",
                   "--archetype", "aquilon", "--personality", "inventory",
                   "--osname", "linux", "--osversion", osver,
                   "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--ip", self.net["cards_net"].usable[0],
                   "--prefix", "cardshost"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "There is no default DNS domain configured for "
                         "rack cards1.  Please specify --dns_domain.",
                         command)

    def test_172_cleanup(self):
        self.noouttest(["del_machine", "--machine", "cardsmachine"])
        self.net.dispose_network(self, "cards_net")

    def test_180_add_utmc8_vmhosts(self):
        pri_net = self.net["ut14_net"]
        storage_net = self.net["vm_storage_net"]
        mgmt_net = self.net["ut14_oob"]
        for i in range(0, 2):
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 80)
            machine = "ut14s1p%d" % i
            ip = pri_net.usable[i]
            eth0_mac = ip.mac
            eth1_ip = storage_net.usable[i + 26]
            eth1_mac = eth1_ip.mac
            mgmt_ip = mgmt_net.usable[i]

            self.create_host(hostname, ip, machine,
                             model="dl360g9", rack="ut14",
                             eth0_mac=eth0_mac,
                             eth1_mac=eth1_mac, eth1_ip=eth1_ip,
                             manager_iface="mgmt0", manager_ip=mgmt_ip,
                             osname="esxi", osversion="5.0.0",
                             archetype="vmhost", personality="vulcan2-server-dev")

    def test_185_add_utmc9_vmhosts(self):
        # This machine will be moved into the right rack later
        self.create_host("evh82.aqd-unittest.ms.com",
                         self.net["ut14_net"].usable[2],
                         "ut14s1p2", model="dl360g9", rack="ut3",
                         manager_iface="mgmt0",
                         manager_ip=self.net["ut14_oob"].usable[2],
                         archetype="vmhost", personality="vulcan-local-disk",
                         osname="esxi", osversion="5.0.0",
                         domain="alt-unittest")
        self.create_host("evh83.aqd-unittest.ms.com",
                         self.net["ut14_net"].usable[3],
                         "ut14s1p3", model="dl360g9", rack="ut14",
                         manager_iface="mgmt0",
                         manager_ip=self.net["ut14_oob"].usable[3],
                         archetype="vmhost", personality="vulcan-local-disk",
                         osname="esxi", osversion="5.0.0",
                         domain="alt-unittest")

    def test_200_machine_reuse(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["add", "host", "--hostname", "used-already.one-nyp.ms.com",
                   "--ip", ip, "--machine", "ut3c5n10", "--domain", "unittest",
                   "--archetype", "aquilon",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 is already allocated to "
                         "host unittest02.one-nyp.ms.com", command)

    def test_200_show_host_bad_domain(self):
        command = "show host --hostname aquilon00.one-nyp"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DNS Domain one-nyp not found.", command)

    def test_200_no_interface(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["add", "host", "--hostname", "unittest03.aqd-unittest.ms.com",
                   "--ip", ip, "--machine", "ut3c1n9",
                   "--domain", "unittest", "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "You have specified an IP address for the host, but "
                         "machine unittest03.aqd-unittest.ms.com does not have "
                         "a bootable interface.",
                         command)

    def test_300_populate_hp_rack_hosts(self):
        # This gives us server1.aqd-unittest.ms.com through server10
        # and aquilon60.aqd-unittest.ms.com through aquilon100
        # It also needs to run *after* the testadd* methods above
        # as some of them rely on a clean IP space for testing the
        # auto-allocation algorithms.
        # I stole the last 2 hp rack hosts for default host
        # aquilon63.aqd-unittest.ms.com & aquilon64.aqd-unittest.ms.com are
        # reserved for manage tests.
        servers = 0
        net = self.net["hp_eth0"]
        mgmt_net = self.net["hp_mgmt"]
        # number 50 is in use by the tor_switch.
        for i in range(51, 100):
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
                personality = "utpers-prod"
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
                personality = None
            port = i - 50
            machine = "ut9s03p%d" % port
            self.create_host(hostname, net.usable[port], machine, rack="ut9",
                             model="bl460cg8", sandbox="%s/utsandbox" % self.user,
                             manager_iface="ilo",
                             manager_ip=mgmt_net.usable[port],
                             personality=personality)

    def test_305_search_sandbox_used(self):
        command = ["search_sandbox", "--used"]
        out = self.commandtest(command)
        self.matchoutput(out, "utsandbox", command)
        self.matchclean(out, "camelcasetest1", command)

    def test_305_search_sandbox_unused(self):
        command = ["search_sandbox", "--unused"]
        out = self.commandtest(command)
        self.matchclean(out, "utsandbox", command)
        self.matchoutput(out, "camelcasetest1", command)
        self.matchoutput(out, "camelcasetest2", command)
        self.matchoutput(out, "changetest1", command)
        self.matchoutput(out, "othersandbox", command)

    def test_310_populate_ut10_hosts(self):
        # These are used in add_virtual_hardware:
        # evh1.aqd-unittest.ms.com
        # evh2.aqd-unittest.ms.com
        # evh3.aqd-unittest.ms.com
        # evh4.aqd-unittest.ms.com
        # evh5.aqd-unittest.ms.com
        # evh6.aqd-unittest.ms.com
        # evh7.aqd-unittest.ms.com
        # evh8.aqd-unittest.ms.com
        # evh9.aqd-unittest.ms.com
        # This is used for utmc7 and update_machine testing:
        # evh10.aqd-unittest.ms.com
        # The other hosts are left for future use.
        eth0_net = self.net["ut10_eth0"]
        eth1_net = self.net["ut10_eth1"]
        mgmt_net = self.net["ut10_oob"]
        # number 100 is in use by the tor_switch.
        for i in range(101, 111):
            port = i - 100
            hostname = "evh%d.aqd-unittest.ms.com" % port
            machine = "ut10s04p%d" % port
            ip = eth0_net.usable[port]
            mgmt_ip = mgmt_net.usable[port]
            eth0_mac = ip.mac
            eth1_mac = eth1_net.usable[port].mac
            # The virtual machine tests require quite a bit of memory...
            self.create_host(hostname, ip, machine,
                             model="dl360g9", memory=81920, rack="ut10",
                             cpuname="e5-2660-v3", cpucount=2,
                             eth0_mac=eth0_mac, eth1_mac=eth1_mac,
                             manager_iface="mgmt0", manager_ip=mgmt_ip,
                             archetype="vmhost",
                             personality="vulcan-10g-server-prod",
                             osname="esxi", osversion="5.0.0")

    def test_320_add_10gig_racks(self):
        for port in range(1, 13):
            for (template, rack, offset) in [('ut11s01p%d', "ut11", 0),
                                             ('ut12s02p%d', "ut12", 12)]:
                machine = template % port
                # Both counts would start at 0 except the tor_net has two
                # switches taking IPs.
                i = port + 1 + offset
                j = port - 1 + offset
                eth0_mac = self.net["vmotion_net"].usable[i].mac
                eth1_mac = self.net["vm_storage_net"].usable[j].mac
                self.create_machine_dl360g9(machine, rack=rack,
                                            eth0_mac=eth0_mac,
                                            eth1_mac=eth1_mac,
                                            eth1_pg="storage-v701")

    def test_321_auxiliary_no_host(self):
        # Test port group based IP address allocation when there is no host yet
        command = ["add_interface_address", "--machine", "ut11s01p1",
                   "--interface", "eth1", "--autoip",
                   "--fqdn", "evh51-e1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine ut11s01p1 does not have a host, assigning an "
                         "IP address based on port group membership is not "
                         "possible.",
                         command)

    def test_322_populate_10gig_rack_hosts(self):
        # Assuming evh11 - evh50 will eventually be claimed above.
        net = self.net["vmotion_net"]
        for i in range(1, 25):
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            manager = "evh%dr.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                port = i
                machine = "ut11s01p%d" % port
                mgmt_net = self.net["ut11_oob"]
            else:
                port = i - 12
                machine = "ut12s02p%d" % port
                mgmt_net = self.net["ut12_oob"]
            self.dsdb_expect_add(hostname, net.usable[i + 1], "eth0",
                                 net.usable[i + 1].mac)
            self.dsdb_expect_add(manager, mgmt_net[port], "mgmt0",
                                 mgmt_net[port].mac)
            command = ["add", "host", "--hostname", hostname, "--autoip",
                       "--machine", machine,
                       "--domain", "unittest",
                       "--osname", "esxi", "--osversion", "5.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan-10g-server-prod"]
            self.noouttest(command)
            command = ["add_manager", "--hostname", hostname, "--interface", "mgmt0",
                       "--ip", mgmt_net[port], "--mac", mgmt_net[port].mac]
            self.noouttest(command)
        self.dsdb_verify()

    def test_323_verify_show_ut11s01p1(self):
        command = "show machine --machine ut11s01p1"
        out = self.commandtest(command.split())
        self.matchoutput(out,
                         "Last switch poll: "
                         "ut01ga2s01.aqd-unittest.ms.com port 1 [",
                         command)

    def test_323_verify_show_ut11s01p1_proto(self):
        command = ["show_machine", "--machine", "ut11s01p1", "--format", "proto"]
        machine = self.protobuftest(command, expect=1)[0]
        ifaces = {iface.device: iface for iface in machine.interfaces}
        self.assertIn("eth1", ifaces)
        self.assertEqual(ifaces["eth1"].port_group_name, "storage-v701")
        # There's no detailed information for phys machines
        self.assertEqual(ifaces["eth1"].port_group_usage, "")
        self.assertEqual(ifaces["eth1"].port_group_tag, 0)

    def test_325_verify_cat_ut11s01p1(self):
        command = "cat --machine ut11s01p1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\);'
                          % self.net["vmotion_net"].usable[2].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"port_group", "storage-v701"\s*\);'
                          % self.net["vm_storage_net"].usable[0].mac,
                          command)

    def test_325_verify_show_host_proto(self):
        # We had a bug where a dangling interface with no IP address
        # assigned would cause show host --format=proto to fail...
        command = ["show_host", "--format=proto",
                   "--hostname=evh1.aqd-unittest.ms.com"]
        host = self.protobuftest(command, expect=1)[0]
        self.assertEqual(host.fqdn, "evh1.aqd-unittest.ms.com")
        self.assertEqual(host.archetype.name, "vmhost")
        self.assertEqual(host.personality.archetype.name, "vmhost")
        self.assertEqual(host.operating_system.archetype.name, "vmhost")
        self.assertEqual(host.operating_system.name, "esxi")
        self.assertEqual(host.operating_system.version, "5.0.0")
        self.assertEqual(host.ip, str(self.net["ut10_eth0"].usable[1]))
        self.assertEqual(host.machine.name, "ut10s04p1")
        self.assertEqual(len(host.machine.interfaces), 3)
        self.assertEqual(host.machine.location.name, 'ut10')
        self.assertEqual(' '.join('%s:%s' % (str(loc.location_type),
                                             str(loc.name))
                                  for loc in host.machine.location.parents),
                         "company:ms hub:ny continent:na country:us "
                         "campus:ny city:ny building:ut")
        eth0_net = self.net["ut10_eth0"]
        mgmt_net = self.net["ut10_oob"]
        for i in host.machine.interfaces:
            if i.device == 'eth0':
                self.assertEqual(i.ip, str(eth0_net.usable[1]))
                self.assertEqual(i.mac, str(eth0_net.usable[1].mac))
                # We're not using this field anymore...
                self.assertEqual(i.network_id, 0)
            elif i.device == 'eth1':
                self.assertEqual(i.ip, "")
                self.assertEqual(i.network_id, 0)
            elif i.device == 'mgmt0':
                self.assertEqual(i.ip, str(mgmt_net.usable[1]))
                self.assertEqual(i.mac, str(mgmt_net.usable[1].mac))
            else:
                self.fail("Unrecognized interface '%s'" % i.device)

    def test_400_add_utnotify(self):
        hostname = self.config.get("unittest", "hostname")
        # We _could_ also look up the real address of the host...
        self.dsdb_expect_add(hostname, "127.0.0.1", "eth0",
                             self.net["tor_net_0"].usable[8].mac)
        self.noouttest(["add", "host",
                        "--hostname", hostname,
                        "--ip", "127.0.0.1", "--machine", "ut8s02p6",
                        "--domain", "unittest", "--buildstatus", "ready",
                        "--archetype", "aquilon",
                        "--personality", "compileserver"])
        command = ["bind", "server", "--service", "utnotify",
                   "--instance", "localhost", "--hostname", hostname]
        out = self.statustest(command)
        self.matchoutput(out, "Warning: Host %s is missing the following "
                         "required services" % hostname, command)

    def test_410_add_afsbynet(self):
        ip = self.net["netsvcmap"].usable[0]
        self.create_host("afs-by-net.aqd-unittest.ms.com", ip, "ut3c5n11",
                         model="hs21-8853", chassis="ut3c5", slot=11,
                         personality="compileserver",
                         comments="For network based service mappings")

    def test_420_add_netmappers(self):
        ip = self.net["netperssvcmap"].usable[0]
        self.create_host("netmap-pers.aqd-unittest.ms.com", ip, "ut3c5n12",
                         model="hs21-8853", chassis="ut3c5", slot=12,
                         personality="utpers-dev", personality_stage="next",
                         comments="For net/pers based service mappings")

    def test_430_add_utinfra1(self):
        eth0_ip = self.net["unknown0"].usable[33]
        eth1_ip = self.net["unknown1"].usable[34]
        ip = self.net["zebra_vip"].usable[0]
        self.create_host("infra1.aqd-unittest.ms.com", ip, "ut3c5n13",
                         model="utrackmount", chassis="ut3c5", slot=13,
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=eth0_ip.mac, eth0_ip=eth0_ip,
                         eth0_fqdn="infra1-e0.aqd-unittest.ms.com",
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="infra1-e1.aqd-unittest.ms.com",
                         zebra=True, ipfromtype='localvip', personality="utpers-prod")

    def test_431_add_utinfra2(self):
        eth0_ip = self.net["unknown0"].usable[38]
        eth1_ip = self.net["unknown1"].usable[37]
        ip = self.net["zebra_vip"].usable[1]
        self.create_host("infra2.aqd-unittest.ms.com", ip, "ut3c5n14",
                         model="utrackmount", chassis="ut3c5", slot=14,
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=eth0_ip.mac, eth0_ip=eth0_ip,
                         eth0_fqdn="infra2-e0.aqd-unittest.ms.com",
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="infra2-e1.aqd-unittest.ms.com",
                         zebra=True, ipfromtype='localvip', personality="utpers-prod")

    def test_435_add_npinfra1(self):
        # FIXME: use networks from np
        eth0_ip = self.net["unknown0"].usable[35]
        eth1_ip = self.net["unknown1"].usable[36]
        ip = self.net["zebra_vip2"].usable[0]
        self.create_host("infra1.one-nyp.ms.com", ip, "np3c5n13",
                         model="utrackmount", chassis="np3c5", slot=13,
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=eth0_ip.mac, eth0_ip=eth0_ip,
                         eth0_fqdn="infra1-e0.one-nyp.ms.com",
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="infra1-e1.one-nyp.ms.com",
                         zebra=True, ipfromtype='vip', personality="utpers-prod")

    def test_436_add_npinfra2(self):
        # FIXME: use networks from np
        eth0_ip = self.net["unknown0"].usable[43]
        eth1_ip = self.net["unknown1"].usable[39]
        ip = self.net["zebra_vip2"].usable[1]
        self.create_host("infra2.one-nyp.ms.com", ip, "np3c5n14",
                         model="utrackmount", chassis="np3c5", slot=14,
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=eth0_ip.mac, eth0_ip=eth0_ip,
                         eth0_fqdn="infra2-e0.one-nyp.ms.com",
                         eth1_mac=eth1_ip.mac, eth1_ip=eth1_ip,
                         eth1_fqdn="infra2-e1.one-nyp.ms.com",
                         zebra=True, ipfromtype='vip', personality="utpers-prod")

    def test_440_add_jack_host(self):
        ip = self.net["tor_net_0"].usable[9]
        self.create_host("jack.cards.example.com", ip, "jack",
                         model="utrackmount", rack="cards1",
                         cpuname="utcpu", cpucount=2, memory=65536,
                         sda_size=600, sda_controller="sas",
                         eth0_mac=ip.mac, eth0_comments="interface for jack",
                         grn="grn:/example/cards", domain="unittest",
                         personality="compileserver")

    def test_445_verify_jack_grn(self):
        command = "show host --hostname jack.cards.example.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Owned by GRN: grn:/example/cards", command)
        self.matchoutput(out, "Used by GRN: grn:/example/cards", command)

    def test_445_verify_show_host_jack_grns(self):
        ip = self.net["tor_net_0"].usable[9]
        command = ["show_host", "--grns", "--hostname=jack.cards.example.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Primary Name: jack.cards.example.com [%s]" % ip,
                         command)
        self.matchoutput(out, "Owned by GRN: grn:/example/cards", command)
        self.matchoutput(out, "Used by GRN: grn:/example/cards [target: esp]", command)

    def _prepare_for_500(self, dns_domain):
        cases = {'wrong': {'building': 'ut'}, 'right': {'building': 'cards'}}
        for case in cases:
            cases[case]['dns_domain'] = dns_domain
            for k in ('desk', 'machine', 'prefix', 'net'):
                cases[case][k] = '{}{}'.format(case, k)
            cases[case]['net'] = '{}net'.format(case)
            cases[case]['host'] = '{}1'.format(cases[case]['prefix'])
            cases[case]['fqhn'] = '{}.{}'.format(
                cases[case]['host'], cases[case]['dns_domain'])
            net = self.net.allocate_network(
                self, cases[case]['net'], 28, 'unknown',
                'building', cases[case]['building'])
            cases[case]['mac'] = net.usable[0].mac
            cases[case]['ip'] = net.usable[0]
            if case == 'right':
                # Set the default DNS domain for the right building.
                command = ['update_building',
                           '--building', cases[case]['building'],
                           '--default_dns_domain', dns_domain]
                self.successtest(command)
            command = ['add_desk', '--desk', cases[case]['desk'],
                       '--building', cases[case]['building']]
            self.successtest(command)
            self.create_machine_dl360g9(
                cases[case]['machine'], desk=cases[case]['desk'],
                eth0_mac=cases[case]['mac'])
        return cases

    def _clean_up_after_500(self, cases):
        # Clean up.
        for case in cases:
            command = ['del_host', '--hostname={}'.format(cases[case]['fqhn'])]
            self.dsdb_expect_delete(cases[case]['ip'])
            self.successtest(command)
            self.noouttest(['del_machine',
                            '--machine', cases[case]['machine']])
            self.net.dispose_network(self, cases[case]['net'])
            command = ['del_desk', '--desk', cases[case]['desk']]
            self.successtest(command)
            if case == 'right':
                # Unset the default DNS domain for the right building.
                command = ['update_building',
                           '--building', cases[case]['building'],
                           '--default_dns_domain', '']
                self.successtest(command)

    def verify_dns_domain_for_buildings(self, extend_command):
        # Set up.
        dns_domain = 'cards.example.com'
        cases = self._prepare_for_500(dns_domain)
        osver = self.config.get('unittest', 'linux_version_curr')
        common = ['add_host', '--domain', 'unittest', '--archetype', 'aquilon',
                  '--osname', 'linux', '--osversion', osver]
        # Test.
        for case in cases:
            command = common[:]
            command.extend(['--ip', cases[case]['ip'],
                            '--machine', cases[case]['machine']])
            extend_command(command, cases[case])
            self.dsdb_expect_add(cases[case]['fqhn'], cases[case]['ip'],
                                 'eth0', cases[case]['mac'])
            if case == 'right':
                # Try to add a host that uses a DNS domain used as the default
                # for the building in which the machine is located. This should
                # succeed.
                self.successtest(command)
                # After leaving this conditional, verify if the right machine
                # without --force_dns_domain worked.
            else:
                # Try to add a host that uses a DNS domain used as the default
                # DNS domain for a building other than the one in which the
                # machine is located.  This should fail.
                # Verify if the wrong machine without --force_dns_domain failed
                # and suggested the use of --force_dns_domain to override.
                failing_command = command[:]
                out = self.badrequesttest(failing_command)
                self.searchoutput(
                    out,
                    (r'DNS domain "' + dns_domain + r'" is already.*'
                     + r'being .* other buildings \(e.g. [^)]*'
                     + cases['right']['building']
                     + r'.*The machine .* is located in building "'
                     + cases[case]['building']
                     + r'".* not associated with this domain'
                     + r'.* use --force_dns_domain.*'),
                    failing_command)
                # Try to add a host that uses a DNS domain used as the default
                # DNS domain for a building other than the one in which the
                # machine is located.  Use the --force_dns_domain switch.  This
                # should succeed.
                succeeding_command = failing_command[:]
                succeeding_command.append('--force_dns_domain')
                self.successtest(succeeding_command)
                # After leaving this conditional, verify if the wrong machine
                # with --force_dns_domain worked.
            # Verify if the right machine without --force_dns_domain and/or
            # the wrong machine with --force_dns_domain worked.
            verify_command = ['show_host', '--format=proto',
                              '--hostname={}'.format(cases[case]['fqhn'])]
            host = self.protobuftest(verify_command, expect=1)[0]
            self.assertEqual(host.hostname, cases[case]['host'])
            self.assertEqual(host.dns_domain, cases[case]['dns_domain'])
            self.assertEqual(host.fqdn, cases[case]['fqhn'])
        # Clean up.
        self._clean_up_after_500(cases)

    def test_500_verify_hostname_for_building(self):
        def extend_command(command, case_data):
            command.extend(['--hostname', case_data['fqhn']])
        self.verify_dns_domain_for_buildings(extend_command=extend_command)

    def test_500_verify_dns_domain_with_prefix_for_building(self):
        def extend_command(command, case_data):
            command.extend(['--prefix', case_data['prefix'],
                            '--dns_domain', case_data['dns_domain']])
        self.verify_dns_domain_for_buildings(extend_command=extend_command)

    def test_800_verify_host_all(self):
        command = ["show", "host", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "afs-by-net.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest15.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest16.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest17.aqd-unittest.ms.com", command)
        self.matchoutput(out, "server1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "aquilon61.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh51.aqd-unittest.ms.com", command)
        self.matchoutput(out, "test-aurora-default-os.ms.com", command)
        self.matchoutput(out, "test-windows-default-os.msad.ms.com", command)
        self.matchoutput(out, "filer1.ms.com", command)
        self.matchoutput(out, "f5test.aqd-unittest.ms.com", command)

    def test_800_verify_host_all_proto(self):
        command = ["show", "host", "--all", "--format", "proto"]
        hostlist = self.protobuftest(command)
        hostnames = set(host_msg.hostname for host_msg in hostlist)
        for hostname in ("afs-by-net.aqd-unittest.ms.com",
                         "unittest02.one-nyp.ms.com",
                         "unittest15.aqd-unittest.ms.com",
                         "unittest16.aqd-unittest.ms.com",
                         "unittest17.aqd-unittest.ms.com",
                         "server1.aqd-unittest.ms.com",
                         "aquilon61.aqd-unittest.ms.com",
                         "evh1.aqd-unittest.ms.com",
                         "evh51.aqd-unittest.ms.com",
                         "test-aurora-default-os.ms.com",
                         "test-windows-default-os.msad.ms.com",
                         "filer1.ms.com",
                         "f5test.aqd-unittest.ms.com"):
            self.assertIn(hostname, hostnames)

    def test_800_verify_host_list(self):
        hosts = ["unittest15.aqd-unittest.ms.com",
                 "unittest16.aqd-unittest.ms.com",
                 "filer1.ms.com"]
        scratchfile = self.writescratch("show_host_list", "\n".join(hosts))
        command = ["show_host", "--list", scratchfile]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut8s02p1", command)
        self.matchoutput(out, "Machine: ut8s02p2", command)
        self.matchoutput(out, "Machine: filer1", command)
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut10s04", command)

    def test_800_show_ut3c5(self):
        ip = self.net["unknown0"].usable[6]
        hostname = self.config.get("unittest", "hostname")
        command = ["show_chassis", "--chassis", "ut3c5"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Chassis: ut3c5
              Primary Name: ut3c5.aqd-unittest.ms.com [%s]
              Building: ut
              Bunker: zebrabucket.ut
              Campus: ny
              City: ny
              Continent: na
              Country: us
              Hub: ny
              Organization: ms
              Rack: ut3
                Row: a
                Column: 3
                Fullname: ut3
              Room: utroom1
              Vendor: hp Model: c-class
                Model Type: chassis
              Serial: ABC5678
              Comments: Some new chassis comments
              Owned by GRN: grn:/ms/ei/aquilon/aqd
              Interface: oa %s
                Type: oa
                Network Environment: internal
                Provides: ut3c5.aqd-unittest.ms.com [%s]
              Slot #2 (type: machine): ut3c5n2 (unittest20.aqd-unittest.ms.com)
              Slot #3 (type: machine): ut3c5n3 (unittest21.aqd-unittest.ms.com)
              Slot #4 (type: machine): ut3c5n4 (unittest22.aqd-unittest.ms.com)
              Slot #5 (type: machine): ut3c5n5 (unittest23.aqd-unittest.ms.com)
              Slot #7 (type: machine): ut3c5n7 (unittest25.aqd-unittest.ms.com)
              Slot #8 (type: machine): ut3c5n8 (unittest26.aqd-unittest.ms.com)
              Slot #10 (type: machine): ut3c5n10 (unittest02.one-nyp.ms.com)
              Slot #11 (type: machine): ut3c5n11 (afs-by-net.aqd-unittest.ms.com)
              Slot #12 (type: machine): ut3c5n12 (netmap-pers.aqd-unittest.ms.com)
              Slot #13 (type: machine): ut3c5n13 (infra1.aqd-unittest.ms.com)
              Slot #14 (type: machine): ut3c5n14 (infra2.aqd-unittest.ms.com)
              Slot #16 (type: machine): ut3c5n16 (no hostname)
              Slot #1 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)
              Slot #2 (type: network_device): ut3c5netdev1 (ut3c5netdev1.aqd-unittest.ms.com)
              Slot #3 (type: network_device): Empty
              Slot #5 (type: network_device): ut3c5netdev2 (ut3c5netdev2.aqd-unittest.ms.com)
            """ % (ip, ip.mac, ip),
            command)

    def test_801_show_ut8s02p6(self):
        hostname = self.config.get("unittest", "hostname")
        command = ["show_machine", "--machine", "ut8s02p6"]
        out = self.commandtest(command)
        self.matchoutput(out, "Provides: %s [127.0.0.1]" % hostname, command)

    def test_805_ipfromtype_host_setup(self):
        # Reuse host in bunker bucket2.ut
        command = ["show", "host", "--hostname", "aquilon67.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bunker: bucket2.ut", command)
        self.dsdb_expect_delete(self.net["hp_eth0"].usable[17])
        self.statustest(["del_host", "--hostname", "aquilon67.aqd-unittest.ms.com"])
        command = ["search", "network", "--type", "localvip", "--exact_location", "--bunker", "bucket2.ut", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bunker: bucket2.ut", command)
        self.matchoutput(out, "Network: ut_bucket2_localvip", command)
        self.dsdb_verify()

    def test_810_ipfromtype_host(self):
        # Reuse host in bunker bucket2.ut
        ip = self.net["ut_bucket2_localvip"].usable[0]
        mac = self.net["hp_eth0"].usable[17].mac
        self.dsdb_expect_add("aquilon67.aqd-unittest.ms.com",
                             ip, "eth0",
                             mac)
        self.noouttest(["add_host", "--hostname", "aquilon67.aqd-unittest.ms.com",
                        "--archetype", "aquilon",
                        "--machine", "ut9s03p17",
                        "--ipfromtype", "localvip", "--sandbox", "%s/utsandbox" % self.user])
        self.dsdb_verify()
        command = ["show", "host", "--hostname", "aquilon67.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Provides: aquilon67.aqd-unittest.ms.com [{}]".format(ip), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
