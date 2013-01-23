#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the make command."""

import os
import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestMake(TestBrokerCommand):

    # network based service mappings
    def testmakeafsbynet_1_checkloc(self):
        # Must by issued before map service.
        command = ["make", "--hostname", "afs-by-net.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testmakeafsbynet_2_mapservice(self):
        ip = self.net.netsvcmap.subnet()[0].ip

        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "afs", "--instance", "afs-by-net"])
        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "afs", "--instance", "afs-by-net2"])

    def testmakeafsbynet_3_verifymapservice(self):
        ip = self.net.netsvcmap.subnet()[0].ip

        command = ["show_map", "--service=afs", "--instance=afs-by-net",
                   "--networkip=%s" % ip]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: afs "
                         "Instance: afs-by-net Map: Network netsvcmap",
                         command)

    def testmakeafsbynet_3_verifymapservice_proto(self):
        ip = self.net.netsvcmap.subnet()[0].ip

        command = ["show_map", "--service=afs", "--instance=afs-by-net",
                   "--networkip=%s" % ip, "--format=proto"]
        out = self.commandtest(command)
        servicemaplist = self.parse_servicemap_msg(out, expect=1)
        service_map = servicemaplist.servicemaps[0]
        self.failUnlessEqual(service_map.network.ip, str(ip))
        self.failUnlessEqual(service_map.network.env_name, 'internal')
        self.failUnlessEqual(service_map.service.name, 'afs')
        self.failUnlessEqual(service_map.service.serviceinstances[0].name,
                             'afs-by-net')

    def testmakeafsbynet_4_make(self):
        command = ["make", "--hostname", "afs-by-net.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/afs-by-net", command)

    def testmakeafsbynet_5_mapconflicts(self):
        ip = self.net.netsvcmap.subnet()[0].ip

        command = ["map", "service", "--networkip", ip,
                        "--service", "afs", "--instance", "afs-by-net",
                        "--building", "whatever"]
        out = self.badoptiontest(command)

        self.matchoutput(out, "networkip conflicts with building", command)

    # network / personality based service mappings

    def testmakenetmappers_1_maplocsvc_nopers(self):
        """Maps a location based service map just to be overridden by a location
        based personality service map"""
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "netmap", "--instance", "q.ny.ms.com"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/netmap/q.ny.ms.com", command)

    def testmakenetmappers_2_maplocsvc_pers(self):
        """Maps a location based personality service map to be overridden by a
        network based personality service map"""
        self.noouttest(["map", "service", "--building", "ut", "--personality",
                        "eaitools", "--archetype", "aquilon",
                        "--service", "netmap", "--instance", "p-q.ny.ms.com"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/netmap/p-q.ny.ms.com", command)

    def testmakenetmappers_3_mapservice(self):
        ip = self.net.netperssvcmap.subnet()[0].ip

        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "netmap", "--instance", "netmap-pers",
                        "--personality", "eaitools",
                        "--archetype", "aquilon"])

    def testmakenetmappers_4_verifymapservice(self):
        ip = self.net.netperssvcmap.subnet()[0].ip

        command = ["show_map", "--service=netmap", "--instance=netmap-pers",
                   "--networkip=%s" % ip, "--personality", "eaitools",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: eaitools "
                         "Service: netmap "
                         "Instance: netmap-pers Map: Network netperssvcmap",
                         command)

    def testmakenetmappers_5_verifymapservice_proto(self):
        ip = self.net.netperssvcmap.subnet()[0].ip

        command = ["show_map", "--service=netmap", "--instance=netmap-pers",
                   "--networkip=%s" % ip, "--personality", "eaitools",
                   "--archetype", "aquilon", "--format=proto"]
        out = self.commandtest(command)
        servicemaplist = self.parse_servicemap_msg(out, expect=1)
        service_map = servicemaplist.servicemaps[0]
        self.failUnlessEqual(service_map.network.ip, str(ip))
        self.failUnlessEqual(service_map.network.env_name, 'internal')
        self.failUnlessEqual(service_map.service.name, 'netmap')
        self.failUnlessEqual(service_map.service.serviceinstances[0].name,
                             'netmap-pers')
        self.failUnlessEqual(service_map.personality.name, 'eaitools')
        self.failUnlessEqual(service_map.personality.archetype.name, 'aquilon')

    def testmakenetmappers_6_make(self):
        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/netmap/netmap-pers", command)

    def testmakevmhosts(self):
        for i in range(1, 6):
            command = ["make", "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                       "--os", "esxi/4.0.0", "--buildstatus", "rebuild"]
            (out, err) = self.successtest(command)
            self.matchclean(err, "removing binding", command)

            self.assert_(os.path.exists(os.path.join(
                self.config.get("broker", "profilesdir"),
                "evh1.aqd-unittest.ms.com%s" % self.profile_suffix)))

            self.failUnless(os.path.exists(os.path.join(
                self.config.get("broker", "builddir"),
                "domains", "unittest", "profiles",
                "evh1.aqd-unittest.ms.com.tpl")))

            servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                      "servicedata")
            results = self.grepcommand(["-rl", "evh%s.aqd-unittest.ms.com" % i,
                                        servicedir])
            self.failUnless(results, "No service plenary data that includes"
                                     "evh%s.aqd-unittest.ms.com" % i)

    def testbados(self):
        command = ["make", "--hostname", "evh1.aqd-unittest.ms.com",
                   "--os", "bad-os-value"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Incorrect value for --os.  Please use "
                         "--osname/--osversion instead.", command)

    def testmake10gighosts(self):
        for i in range(51, 75):
            command = ["make", "--hostname", "evh%s.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)

    def testmakeccisshost(self):
        command = ["make", "--hostname=unittest18.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testmakezebra(self):
        command = ["make", "--hostname", "unittest20.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testverifyunittest20(self):
        eth0_ip = self.net.unknown[11].usable[0]
        eth0_broadcast = self.net.unknown[11].broadcast
        eth0_netmask = self.net.unknown[11].netmask
        eth0_gateway = self.net.unknown[11].gateway

        eth1_ip = self.net.unknown[12].usable[0]
        eth1_broadcast = self.net.unknown[12].broadcast
        eth1_netmask = self.net.unknown[12].netmask
        eth1_gateway = self.net.unknown[12].gateway
        eth1_1_ip = self.net.unknown[12].usable[3]

        hostname_ip = self.net.unknown[13].usable[2]
        zebra2_ip = self.net.unknown[13].usable[1]
        zebra3_ip = self.net.unknown[13].usable[0]

        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "template hostdata/unittest20.aqd-unittest.ms.com;",
                         command)
        self.searchoutput(out,
                          r'"/system/resources/service_address" = '
                          r'push\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/hostname/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"/system/resources/service_address" = '
                          r'push\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/zebra2/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"/system/resources/service_address" = '
                          r'push\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/zebra3/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"/system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s",\s*"%s"\s*\),\s*'
                          r'"eth1", list\(\s*"%s",\s*"%s"\s*\)\s*'
                          r'\);' % (self.net.unknown[11][1],
                                    self.net.unknown[11][2],
                                    self.net.unknown[12][1],
                                    self.net.unknown[12][2]),
                          command)
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e0.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\)\s*' %
                          (eth0_broadcast, eth0_gateway, eth0_ip, eth0_netmask),
                          command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
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
                          r'"network_type", "unknown"\s*\)\s*' %
                          (eth1_broadcast, eth1_1_ip, eth1_netmask,
                           eth1_broadcast, eth1_gateway, eth1_ip, eth1_netmask),
                          command)
        self.matchoutput(out, '"/system/network/default_gateway" = \"%s\";' %
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

    def testmakeunittest21(self):
        command = ["make", "--hostname", "unittest21.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testverifyunittest21(self):
        net = self.net.unknown[11]
        command = ["cat", "--hostname", "unittest21.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/system/network/default_gateway" = \"%s\";' %
                         net.gateway, command)
        self.searchoutput(out,
                          r'"/system/network/routers" = nlist\(\s*'
                          r'"bond0", list\(\s*'
                          r'"%s",\s*"%s"\s*\)\s*\);' % (net[1], net[2]),
                          command)

    def testmakeunittest23(self):
        command = ["make", "--hostname", "unittest23.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testverifyunittest23(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest23.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net.vpls[0]
        ip = net.usable[1]
        router = net[1]
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest23.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "vpls"\s*\)\s*' %
                          (net.broadcast, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"/system/network/default_gateway" = \"%s\";' %
                         router, command)
        self.searchoutput(out,
                          r'"/system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s"\s*\)\s*\);' % router,
                          command)

    def testmakeunittest24(self):
        command = ["make", "--hostname", "unittest24.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testverifyunittest24(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest24.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net.vpls[0]
        ip = net.usable[2]
        router = net[2]
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest24.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "vpls"\s*\)\s*' %
                          (net.broadcast, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"/system/network/default_gateway" = \"%s\";' %
                         router, command)
        self.searchoutput(out,
                          r'"/system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s"\s*\)\s*\);' % router,
                          command)

    def testmakeunittest25(self):
        command = ["make", "--hostname", "unittest25.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testverifyunittest25(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest25.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net.unknown[1]
        ip = net[4]
        router = net[2]
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest25-e1.utcolo.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "utcolo",\s*'
                          r'"network_type", "unknown"\s*\)\s*' %
                          (net.broadcast, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"/system/network/default_gateway" = "%s";' %
                         self.net.unknown[0].gateway, command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMake)
    unittest.TextTestRunner(verbosity=2).run(suite)
