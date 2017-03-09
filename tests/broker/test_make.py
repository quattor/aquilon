#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the make command."""

import os

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestMake(TestBrokerCommand):

    def test_100_make_10gig_hosts(self):
        for i in range(51, 75):
            command = ["make", "--hostname", "evh%s.aqd-unittest.ms.com" % i]
            self.statustest(command)

    # network based service mappings
    def test_110_scope_pre_checks(self):
        # Must by issued before map service.
        command = ["make", "--hostname", "afs-by-net.aqd-unittest.ms.com"]
        self.statustest(command)

        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: afs Instance: q.ny.ms.com",
                         command)

    def test_111_scope_add_network_maps(self):
        ip = list(self.net["netsvcmap"].subnets())[0].ip

        self.noouttest(["map", "service", "--networkip", ip,
                        "--justification", "tcm=12345678",
                        "--service", "afs", "--instance", "afs-by-net"])
        self.noouttest(["map", "service", "--networkip", ip,
                        "--justification", "tcm=12345678",
                        "--service", "afs", "--instance", "afs-by-net2"])

    def test_112_scope_verify_maps(self):
        ip = list(self.net["netsvcmap"].subnets())[0].ip

        command = ["show_map", "--service=afs", "--instance=afs-by-net",
                   "--networkip=%s" % ip]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service: afs Instance: afs-by-net Map: Network netsvcmap",
                         command)

    def test_112_scope_verify_maps_proto(self):
        ip = list(self.net["netsvcmap"].subnets())[0].ip

        command = ["show_map", "--service=afs", "--instance=afs-by-net",
                   "--networkip=%s" % ip, "--format=proto"]
        service_map = self.protobuftest(command, expect=1)[0]
        self.assertEqual(service_map.network.ip, str(ip))
        self.assertEqual(service_map.network.cidr, 27)
        self.assertEqual(service_map.network.type, "unknown")
        self.assertEqual(service_map.network.env_name, 'internal')
        self.assertEqual(service_map.service.name, 'afs')
        self.assertEqual(service_map.service.serviceinstances[0].name,
                         'afs-by-net')

    def test_113_scope_make(self):
        command = ["make", "--hostname", "afs-by-net.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out, "removing binding for service instance afs/q.ny.ms.com",
                         command)
        self.matchoutput(out, "adding binding for service instance afs/afs-by-net",
                         command)

    def test_114_scope_verify(self):
        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        # This can be either afs-by-net or afs-by-net2
        self.matchoutput(out,
                         "Uses Service: afs Instance: afs-by-net",
                         command)

    def test_120_setup(self):
        """Maps a location based service map just to be overridden by a location
        based personality service map"""
        self.noouttest(["map", "service", "--building", "ut",
                        "--justification", "tcm=12345678",
                        "--service", "scope_test", "--instance", "scope-building"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "adding binding for service instance scope_test/scope-building",
                         command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: scope_test Instance: scope-building",
                         command)

    def test_121_environment_precedence(self):
        """Maps a location based environment service map to be overridden by a
        location based personality service map"""
        self.noouttest(["map_service", "--building", "ut",
                        "--host_environment", "dev",
                        "--justification", "tcm=12345678",
                        "--service", "scope_test",
                        "--instance", "target-dev"])
        self.noouttest(["map_service", "--building", "ut",
                        "--host_environment", "qa",
                        "--justification", "tcm=12345678",
                        "--service", "scope_test",
                        "--instance", "target-qa"])

        command = ["show_service", "--service", "scope_test", "--instance", "target-dev"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service Map: Building ut (Host Environment: dev)",
                         command)

        command = ["show_map", "--service", "scope_test", "--instance", "target-dev"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Host Environment: dev Service: scope_test Instance: target-dev Map: Building ut",
                         command)

        command = ["show_map", "--service", "scope_test",
                   "--instance", "target-dev", "--format", "proto"]
        maps = self.protobuftest(command, expect=1)
        self.assertEqual(maps[0].location.name, "ut")
        self.assertEqual(maps[0].location.location_type, "building")
        self.assertEqual(maps[0].host_environment, "dev")
        self.assertEqual(maps[0].personality.name, "")
        self.assertEqual(maps[0].network.ip, "")

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "removing binding for service instance scope_test/scope-building",
                         command)
        self.matchoutput(out,
                         "adding binding for service instance scope_test/target-dev",
                         command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: scope_test Instance: target-dev",
                         command)

    def test_122_environment_override(self):
        self.noouttest(["del_required_service", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--service", "scope_test"])
        self.noouttest(["add_required_service", "--personality", "utpers-dev",
                        "--archetype", "aquilon", "--service", "scope_test",
                        "--environment_override", "qa"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "removing binding for service instance scope_test/target-dev",
                         command)
        self.matchoutput(out,
                         "adding binding for service instance scope_test/target-qa",
                         command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: scope_test Instance: target-qa",
                         command)

        command = ["show_service", "--service", "scope_test"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Required for Personality: utpers-dev Archetype: aquilon\s*'
                          r'Stage: next\s*'
                          r'Environment Override: qa',
                          command)

    def test_123_personality_precedence(self):
        """Maps a location based personality service map to be overridden by a
        network based personality service map"""
        self.noouttest(["map", "service", "--building", "ut", "--personality",
                        "utpers-dev", "--archetype", "aquilon",
                        "--service", "scope_test",
                        "--instance", "target-personality"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "removing binding for service instance scope_test/target-qa",
                         command)
        self.matchoutput(out,
                         "adding binding for service instance scope_test/target-personality",
                         command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: scope_test Instance: target-personality",
                         command)

    def test_124_network_precedence(self):
        ip = list(self.net["netperssvcmap"].subnets())[0].ip

        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "scope_test", "--instance", "scope-network",
                        "--personality", "utpers-dev",
                        "--archetype", "aquilon"])

    def test_125_verify_network_map(self):
        ip = list(self.net["netperssvcmap"].subnets())[0].ip

        command = ["show_map", "--service=scope_test", "--instance=scope-network",
                   "--networkip=%s" % ip, "--personality", "utpers-dev",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: utpers-dev "
                         "Service: scope_test "
                         "Instance: scope-network Map: Network netperssvcmap",
                         command)

    def test_125_verify_network_map_proto(self):
        ip = list(self.net["netperssvcmap"].subnets())[0].ip

        command = ["show_map", "--service=scope_test", "--instance=scope-network",
                   "--networkip=%s" % ip, "--personality", "utpers-dev",
                   "--archetype", "aquilon", "--format=proto"]
        service_map = self.protobuftest(command, expect=1)[0]
        self.assertEqual(service_map.network.ip, str(ip))
        self.assertEqual(service_map.network.cidr, 27)
        self.assertEqual(service_map.network.type, "unknown")
        self.assertEqual(service_map.network.env_name, 'internal')
        self.assertEqual(service_map.service.name, 'scope_test')
        self.assertEqual(service_map.service.serviceinstances[0].name,
                         'scope-network')
        self.assertEqual(service_map.personality.name, 'utpers-dev')
        self.assertEqual(service_map.personality.archetype.name, 'aquilon')

    def test_126_make_network(self):
        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "removing binding for service instance scope_test/target-personality",
                         command)
        self.matchoutput(out,
                         "adding binding for service instance scope_test/scope-network",
                         command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: scope_test Instance: scope-network",
                         command)

    def test_130_make_vm_hosts(self):
        for i in range(1, 6):
            command = ["make", "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                       "--osname", "esxi", "--osversion", "5.0.0"]
            err = self.statustest(command)
            self.matchclean(err, "removing binding", command)

            self.assertTrue(os.path.exists(os.path.join(
                self.config.get("broker", "profilesdir"),
                "evh1.aqd-unittest.ms.com%s" % self.xml_suffix)))

            self.assertTrue(os.path.exists(
                self.build_profile_name("evh1.aqd-unittest.ms.com",
                                        domain="unittest")))

            servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                      "servicedata")
            results = self.grepcommand(["-rl", "evh%s.aqd-unittest.ms.com" % i,
                                        servicedir])
            self.assertTrue(results, "No service plenary data that includes"
                            "evh%s.aqd-unittest.ms.com" % i)

    def test_135_make_utmc9(self):
        command = ["make", "--hostname", "evh82.aqd-unittest.ms.com"]
        self.statustest(command)

        command = ["show", "host", "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Uses Service: vcenter Instance: ut", command)

    def test_140_make_cciss_host(self):
        command = ["make", "--hostname=unittest18.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def test_145_make_aurora(self):
        command = ["make", "--hostname", self.aurora_with_node + ".ms.com"]
        self.statustest(command)

    def test_150_make_zebra(self):
        command = ["make", "--hostname", "unittest20.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def test_151_verify_unittest20(self):
        eth0_ip = self.net["zebra_eth0"].usable[0]
        eth0_broadcast = self.net["zebra_eth0"].broadcast_address
        eth0_netmask = self.net["zebra_eth0"].netmask
        eth0_gateway = self.net["zebra_eth0"].gateway

        eth1_ip = self.net["zebra_eth1"].usable[0]
        eth1_broadcast = self.net["zebra_eth1"].broadcast_address
        eth1_netmask = self.net["zebra_eth1"].netmask
        eth1_gateway = self.net["zebra_eth1"].gateway
        eth1_1_ip = self.net["zebra_eth1"].usable[3]

        hostname_ip = self.net["zebra_vip"].usable[2]
        zebra2_ip = self.net["zebra_vip"].usable[1]
        zebra3_ip = self.net["zebra_vip"].usable[0]

        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template hostdata/unittest20.aqd-unittest.ms.com;",
                         command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/hostname/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/zebra2/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/zebra3/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s",\s*"%s"\s*\),\s*'
                          r'"eth1", list\(\s*"%s",\s*"%s"\s*\)\s*'
                          r'\);' % (self.net["zebra_eth0"][1],
                                    self.net["zebra_eth0"][2],
                                    self.net["zebra_eth1"][1],
                                    self.net["zebra_eth1"][2]),
                          command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e0.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\);' %
                          (eth0_broadcast, eth0_gateway, eth0_ip, eth0_netmask),
                          command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth1" = nlist\(\s*'
                          r'"aliases", nlist\(\s*'
                          r'"e1", nlist\(\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e1-1.aqd-unittest.ms.com",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s"\s*\)\s*\),\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e1.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\);' %
                          (eth1_broadcast, eth1_1_ip, eth1_netmask,
                           eth1_broadcast, eth1_gateway, eth1_ip, eth1_netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         eth0_gateway, command)

        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)
        self.matchclean(out, '"/metadata/template/branch/author"', command)

        command = ["cat", "--service_address", "hostname",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "hostname";', command)
        self.matchoutput(out, '"ip" = "%s";' % hostname_ip, command)
        self.searchoutput(out,
                          r'"interfaces" = list\(\s*"eth0",\s*"eth1"\s*\);',
                          command)
        self.matchoutput(out, '"fqdn" = "unittest20.aqd-unittest.ms.com";',
                         command)

        command = ["cat", "--service_address", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "zebra2";', command)
        self.matchoutput(out, '"ip" = "%s";' % zebra2_ip, command)
        self.searchoutput(out,
                          r'"interfaces" = list\(\s*"eth0",\s*"eth1"\s*\);',
                          command)
        self.matchoutput(out, '"fqdn" = "zebra2.aqd-unittest.ms.com";',
                         command)

        command = ["cat", "--service_address", "zebra3",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "zebra3";', command)
        self.matchoutput(out, '"ip" = "%s";' % zebra3_ip, command)
        self.searchoutput(out,
                          r'"interfaces" = list\(\s*"eth0",\s*"eth1"\s*\);',
                          command)
        self.matchoutput(out, '"fqdn" = "zebra3.aqd-unittest.ms.com";',
                         command)

    def test_152_make_unittest21(self):
        command = ["make", "--hostname", "unittest21.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def test_153_verify_unittest21(self):
        net = self.net["zebra_eth0"]
        command = ["cat", "--hostname", "unittest21.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         net.gateway, command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"bond0", list\(\s*'
                          r'"%s",\s*"%s"\s*\)\s*\);' % (net[1], net[2]),
                          command)

    def test_154_make_unittest23(self):
        command = ["make", "--hostname", "unittest23.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def test_155_verify_unittest23(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest23.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net["vpls"]
        ip = net.usable[1]
        router = net[1]
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest23.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "vpls"\s*\);' %
                          (net.broadcast_address, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         router, command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s"\s*\)\s*\);' % router,
                          command)

    def test_156_make_unittest24(self):
        command = ["make", "--hostname", "unittest24.one-nyp.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def test_157_verify_unittest24(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest24.one-nyp.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net["vpls"]
        ip = net.usable[2]
        router = net[2]
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest24.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "vpls"\s*\);' %
                          (net.broadcast_address, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         router, command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s"\s*\)\s*\);' % router,
                          command)

    def test_158_make_unittest25(self):
        command = ["make", "--hostname", "unittest25.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def test_159_verify_unittest25(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest25.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net["unknown1"]
        ip = net[4]
        router = net[2]
        self.searchoutput(out,
                          r'"system/network/interfaces/eth1" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest25-e1.utcolo.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "utcolo",\s*'
                          r'"network_type", "unknown"\s*\);' %
                          (net.broadcast_address, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = "%s";' %
                         self.net["unknown0"].gateway, command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMake)
    unittest.TextTestRunner(verbosity=2).run(suite)
