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
"""Module for testing the add host command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand
from networktest import DummyIP


class TestAddHost(TestBrokerCommand):

    def testaddutnotify(self):
        hostname = self.config.get("unittest", "hostname")
        # We _could_ also look up the real address of the host...
        self.dsdb_expect_add(hostname, "127.0.0.1", "eth0",
                             self.net["unknown0"].usable[19].mac)
        self.noouttest(["add", "host",
                        "--hostname", hostname,
                        "--ip", "127.0.0.1", "--machine", "ut3c5n6",
                        "--domain", "unittest", "--buildstatus", "ready",
                        "--archetype", "aquilon", "--osname", "linux",
                        "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.noouttest(["bind", "server", "--service", "utnotify",
                        "--instance", "localhost", "--hostname", hostname])

    def testaddunittest02(self):
        ip = self.net["unknown0"].usable[0]
        self.dsdb_expect_add("unittest02.one-nyp.ms.com", ip, "eth0", ip.mac,
                             comments="Some machine comments")
        self.noouttest(["add", "host",
                        "--hostname", "unittest02.one-nyp.ms.com", "--ip", ip,
                        "--machine", "ut3c5n10", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testaddafsbynet(self):
        ip = self.net["netsvcmap"].usable[0]
        self.dsdb_expect_add("afs-by-net.aqd-unittest.ms.com", ip, "eth0", ip.mac,
                             comments="For network based service mappings")
        self.noouttest(["add", "host",
                        "--hostname", "afs-by-net.aqd-unittest.ms.com",
                        "--ip", ip,
                        "--machine", "ut3c5n11", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testaddnetmappers(self):
        ip = self.net["netperssvcmap"].usable[0]
        self.dsdb_expect_add("netmap-pers.aqd-unittest.ms.com", ip, "eth0", ip.mac,
                             comments="For net/pers based service mappings")
        self.noouttest(["add", "host",
                        "--hostname", "netmap-pers.aqd-unittest.ms.com",
                        "--ip", ip,
                        "--machine", "ut3c5n12", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "eaitools"])
        self.dsdb_verify()

    def testaddjackhost(self):
        ip = self.net["unknown0"].usable[17]
        self.dsdb_expect_add("jack.cards.example.com", ip, "eth0", ip.mac,
                             comments="interface for jack")
        self.noouttest(["add", "host",
                        "--hostname", "jack.cards.example.com",
                        "--ip", ip, "--grn", "grn:/example/cards",
                        "--machine", "jack", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyjackgrn(self):
        command = "show host --hostname jack.cards.example.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Owned by GRN: grn:/example/cards", command)
        self.matchoutput(out, "Used by GRN: grn:/example/cards", command)

    def testmachinereuse(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["add", "host", "--hostname", "used-already.one-nyp.ms.com",
                   "--ip", ip, "--machine", "ut3c5n10", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 is already allocated to "
                         "host unittest02.one-nyp.ms.com", command)

    def testverifyaddunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net["unknown0"].usable[0],
                         command)
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Version: 5.0.1-x86_64", command)
        self.matchoutput(out, "Advertise Status: False", command)

    def testverifyaddafsbynet(self):
        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: afs-by-net.aqd-unittest.ms.com [%s]" %
                         self.net["netsvcmap"].usable[0],
                         command)
        self.matchoutput(out, "Blade: ut3c5n11", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Version: 5.0.1-x86_64", command)
        self.matchoutput(out, "Advertise Status: False", command)

    def testverifyunittest02machine(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net["unknown0"].usable[0],
                         command)

    def testverifyaddafsbynetut3c5n11(self):
        command = "show machine --machine ut3c5n11"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: afs-by-net.aqd-unittest.ms.com [%s]" %
                         self.net["netsvcmap"].usable[0],
                         command)

    def testverifyaddafsbynetut3c5n12(self):
        command = "show machine --machine ut3c5n12"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: netmap-pers.aqd-unittest.ms.com [%s]" %
                         self.net["netperssvcmap"].usable[0],
                         command)

    def testverifyhostdns(self):
        command = "search dns --fqdn unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testshowhostbaddomain(self):
        command = "show host --hostname aquilon00.one-nyp"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DNS Domain one-nyp not found.", command)

    def testverifyunittest02proto(self):
        command = "show host --hostname unittest02.one-nyp.ms.com --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_hostlist_msg(out)

    def testaddunittest15(self):
        ip = self.net["tor_net_0"].usable[1]
        self.dsdb_expect_add("unittest15.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "host",
            "--hostname", "unittest15.aqd-unittest.ms.com",
            "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
            "--ipalgorithm", "max",
            "--osname", "linux", "--osversion", "5.0.1-x86_64",
            "--machine", "ut8s02p1", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])
        self.dsdb_verify()

    def testverifyunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest15.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_0"].usable[1],
                         command)
        self.matchoutput(out, "Personality: inventory", command)

    def testaddunittest16bad(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", self.net["dyndhcp1"].usable[-1],
                   "--ipalgorithm", "max",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Failed to find an IP that is suitable for "
                         "--ipalgorithm=max.  Try an other algorithm as there "
                         "are still some free addresses.",
                         command)

    def testaddunittest16badip(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ip", "not-an-ip-address",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Expected an IPv4 address for --ip: "
                         "not-an-ip-address",
                         command)

    def testaddunittest16baddomain(self):
        net = self.net["tor_net_0"]
        command = ["add", "host", "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", net.usable[0], "--ipalgorithm", "lowest",
                   "--machine", "ut8s02p2", "--domain", "nomanage",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Adding hosts to domain nomanage "
                         "is not allowed.", command)

    def testaddunittest16good(self):
        net = self.net["tor_net_0"]
        self.dsdb_expect_add("unittest16.aqd-unittest.ms.com", net.usable[2],
                             "eth0", net.usable[2].mac)
        self.noouttest(["add", "host",
                        "--hostname", "unittest16.aqd-unittest.ms.com",
                        "--ipfromip", net.usable[0], "--ipalgorithm", "lowest",
                        "--machine", "ut8s02p2", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest16.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_0"].usable[2],
                         command)
        self.matchoutput(out, "Personality: compileserver", command)

    #test aquilons default linux/5.0.1-x86_64
    def testaddunittest17(self):
        ip = self.net["tor_net_0"].usable[3]
        self.dsdb_expect_add("unittest17.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "host",
            "--hostname", "unittest17.aqd-unittest.ms.com",
            "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
            "--machine", "ut8s02p3", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])
        self.dsdb_verify()

    def testverifyunittest17(self):
        #verifies default os and personality for aquilon
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest17.aqd-unittest.ms.com [%s]" %
                         self.net["tor_net_0"].usable[3],
                         command)
        self.searchoutput(out,
                          r'Operating System: linux\s*'
                          r'Version: 5\.0\.1-x86_64\s*'
                          r'Archetype: aquilon',
                          command)
        self.matchoutput(out, "Personality: inventory", command)

    def testaddnointerface(self):
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

    def testpopulatehprackhosts(self):
        # This gives us server1.aqd-unittest.ms.com through server10
        # and aquilon60.aqd-unittest.ms.com through aquilon100
        # It also needs to run *after* the testadd* methods above
        # as some of them rely on a clean IP space for testing the
        # auto-allocation algorithms.
        # I stole the last 2 hp rack hosts for default host
        # aquilon63.aqd-unittest.ms.com & aquilon64.aqd-unittest.ms.com are
        # reserved for manage tests.
        servers = 0
        user = self.config.get("unittest", "user")
        net = self.net["hp_eth0"]
        for i in range(51, 100):
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            port = i - 50
            self.dsdb_expect_add(hostname, net.usable[port], "eth0",
                                 net.usable[port].mac)
            command = ["add", "host", "--hostname", hostname,
                       "--ip", net.usable[port],
                       "--machine", "ut9s03p%d" % port,
                       "--sandbox", "%s/utsandbox" % user,
                       "--buildstatus", "build",
                       "--osname", "linux", "--osversion", "5.0.1-x86_64",
                       "--archetype", "aquilon", "--personality", "inventory"]
            self.noouttest(command)
        self.dsdb_verify()

    def testpopulateverarirackhosts(self):
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
        net = self.net["verari_eth0"]
        for i in range(101, 111):
            port = i - 100
            hostname = "evh%d.aqd-unittest.ms.com" % port
            self.dsdb_expect_add(hostname, net.usable[port], "eth0",
                                 net.usable[port].mac)
            command = ["add", "host", "--hostname", hostname,
                       "--ip", net.usable[port],
                       "--machine", "ut10s04p%d" % port,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan-1g-desktop-prod"]
            self.noouttest(command)
        self.dsdb_verify()

    def testpopulate10gigrackhosts(self):
        # Assuming evh11 - evh50 will eventually be claimed above.
        net = self.net["vmotion_net"]
        for i in range(1, 25):
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                port = i
                machine = "ut11s01p%d" % port
            else:
                port = i - 12
                machine = "ut12s02p%d" % port
            self.dsdb_expect_add(hostname, net.usable[i + 1], "eth0",
                                 net.usable[i + 1].mac)
            command = ["add", "host", "--hostname", hostname, "--autoip",
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan-1g-desktop-prod"]
            self.noouttest(command)
        self.dsdb_verify()

    def testpopulate_esx_bcp_clusterhosts(self):
        utnet = self.net["esx_bcp_ut"]
        npnet = self.net["esx_bcp_np"]
        for i in range(25, 49):
            port = i - 24

            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            machine = "ut13s03p%d" % port
            self.dsdb_expect_add(hostname, utnet.usable[port], "eth0",
                                 utnet.usable[port].mac)
            command = ["add", "host", "--hostname", hostname, "--autoip",
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan-1g-desktop-prod"]
            self.noouttest(command)

            hostname = "evh%d.one-nyp.ms.com" % (i + 50)
            machine = "np13s03p%d" % port
            self.dsdb_expect_add(hostname, npnet.usable[port], "eth0",
                                 npnet.usable[port].mac)
            command = ["add", "host", "--hostname", hostname, "--autoip",
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan-1g-desktop-prod"]
            self.noouttest(command)
        self.dsdb_verify()

    def testverifyshowhostproto(self):
        # We had a bug where a dangling interface with no IP address
        # assigned would cause show host --format=proto to fail...
        command = ["show_host", "--format=proto",
                   "--hostname=evh1.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.assertEmptyErr(err, command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.assertEqual(host.fqdn, "evh1.aqd-unittest.ms.com")
        self.assertEqual(host.archetype.name, "vmhost")
        self.assertEqual(host.operating_system.archetype.name, "vmhost")
        self.assertEqual(host.operating_system.name, "esxi")
        self.assertEqual(host.operating_system.version, "4.0.0")
        self.assertEqual(host.ip, str(self.net["verari_eth0"].usable[1]))
        self.assertEqual(host.machine.name, "ut10s04p1")
        self.assertEqual(len(host.machine.interfaces), 2)
        self.assertEqual(host.machine.location.name, 'ut10')
        self.assertEqual(' '.join(['%s:%s' % (str(loc.location_type),
                                              str(loc.name))
                                   for loc in host.machine.location.parents]),
                         "company:ms hub:ny continent:na country:us "
                         "campus:ny city:ny building:ut")
        for i in host.machine.interfaces:
            if i.device == 'eth0':
                self.assertEqual(i.ip, str(self.net["verari_eth0"].usable[1]))
                # We're not using this field anymore...
                self.assertEqual(i.network_id, 0)
            elif i.device == 'eth1':
                self.assertEqual(i.ip, "")
                self.assertEqual(i.network_id, 0)
            else:
                self.fail("Unrecognized interface '%s'" % i.device)

    def testaddhostnousefularchetype(self):
        command = ["add", "host", "--archetype", "filer",
                   "--hostname", "unittest01.one-nyp.ms.com",
                   "--ip", self.net["unknown0"].usable[10],
                   "--domain", "unittest", "--machine", "ut3c1n4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Can not determine a sensible default OS", command)

    def testaddccisshost(self):
        ip = self.net["unknown0"].usable[18]
        self.dsdb_expect_add("unittest18.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        command = ["add", "host", "--archetype", "aquilon",
                   "--hostname", "unittest18.aqd-unittest.ms.com", "--ip", ip,
                   "--domain", "unittest", "--machine", "ut3c1n8"]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddfiler(self):
        ip = self.net["vm_storage_net"].usable[25]
        self.dsdb_expect_add("filer1.ms.com", ip, "v0")
        command = ["add", "host", "--archetype", "filer",
                   "--hostname", "filer1.ms.com", "--ip", ip,
                   "--domain", "unittest", "--machine", "filer1",
                   "--osname=ontap", "--osversion=7.3.3p1"]
        self.noouttest(command)
        self.dsdb_verify()

    #test aurora and windows defaults now
    def testaddauroradefaultos(self):
        ip = self.net["utpgsw0-v710"].usable[-1]
        self.dsdb_expect("show_host -host_name test-aurora-default-os")
        self.noouttest(["add", "host", "--archetype", "aurora",
                        "--hostname", "test-aurora-default-os.ms.com",
                        "--ip", ip, "--domain", "ny-prod", "--machine",
                        "ut8s02p4"])
        self.dsdb_verify()

    def testverifyaddauroradefaultos(self):
        command = "show host --hostname test-aurora-default-os.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: test-aurora-default-os.ms.com", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.searchoutput(out,
                          r'Operating System: linux\s*'
                          r'Version: generic\s*'
                          r'Archetype: aurora',
                          command)

    def testaddwindowsefaultos(self):
        ip = self.net["utpgsw0-v710"].usable[-2]
        self.dsdb_expect_add("test-windows-default-os.msad.ms.com", ip,
                             "eth0", self.net["tor_net_0"].usable[5].mac)
        self.noouttest(["add", "host", "--archetype", "windows",
                        "--hostname", "test-windows-default-os.msad.ms.com",
                        "--ip", ip, "--domain", "ny-prod",
                        "--machine", "ut8s02p5"])
        self.dsdb_verify()

    def testverifyaddwindowsdefaultos(self):
        command = "show host --hostname test-windows-default-os.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: test-windows-default-os.msad.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.searchoutput(out,
                          r'Operating System: windows\s*'
                          r'Version: generic\s*'
                          r'Archetype: windows',
                          command)

    def testaddf5(self):
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

    def testverifyhostall(self):
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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
