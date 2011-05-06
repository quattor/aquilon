#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Module for testing the add host command."""

import unittest
import socket

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddHost(TestBrokerCommand):

    def testaddutnotify(self):
        hostname = socket.getfqdn()
        # We _could_ also look up the real address of the host...
        self.dsdb_expect_add(hostname, "127.0.0.1", "eth0",
                             self.net.unknown[0].usable[19].mac)
        self.noouttest(["add", "host",
                        "--hostname", hostname,
                        "--ip", "127.0.0.1", "--machine", "ut3c5n6",
                        "--domain", "unittest", "--buildstatus", "ready",
                        "--archetype", "aquilon", "--osname", "linux",
                        "--osversion", "4.0.1-x86_64",
                        "--personality", "compileserver"])
        self.noouttest(["bind", "server", "--service", "utnotify",
                        "--instance", "localhost", "--hostname", hostname])

    def testaddunittest02(self):
        ip = self.net.unknown[0].usable[0]
        self.dsdb_expect_add("unittest02.one-nyp.ms.com", ip, "eth0", ip.mac)
        self.noouttest(["add", "host",
                        "--hostname", "unittest02.one-nyp.ms.com", "--ip", ip,
                        "--machine", "ut3c5n10", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testaddjackhost(self):
        ip = self.net.unknown[0].usable[17]
        self.dsdb_expect_add("jack.cards.example.com", ip, "eth0", ip.mac)
        self.noouttest(["add", "host",
                        "--hostname", "jack.cards.example.com",
                        "--ip", ip,
                        "--machine", "jack", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testmachinereuse(self):
        ip = self.net.unknown[0].usable[-1]
        command = ["add", "host", "--hostname", "used-already.one-nyp.ms.com",
                   "--ip", ip, "--machine", "ut3c5n10", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "4.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 is already allocated to "
                         "host unittest02.one-nyp.ms.com", command)

    def testverifyaddunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[0],
                         command)
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Version: 4.0.1-x86_64", command)

    def testverifyunittest02machine(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[0],
                         command)

    def testverifyshowfqdnhost(self):
        command = "show fqdn --fqdn unittest02.one-nyp.ms.com"
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
        ip = self.net.tor_net[0].usable[1]
        self.dsdb_expect_add("unittest15.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        self.noouttest(["add", "host",
            "--hostname", "unittest15.aqd-unittest.ms.com",
            "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
            "--ipalgorithm", "max",
            "--osname", "linux", "--osversion", "4.0.1-x86_64",
            "--machine", "ut8s02p1", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])
        self.dsdb_verify()

    def testverifyunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest15.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[0].usable[1],
                         command)
        self.matchoutput(out, "Personality: inventory", command)

    def testaddunittest16bad(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", self.net.tor_net2[1].usable[-1],
                   "--ipalgorithm", "max",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "4.0.1-x86_64",
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
                   "--osname", "linux", "--osversion", "4.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Expected an IPv4 address for --ip: "
                         "not-an-ip-address",
                         command)

    def testaddunittest16good(self):
        net = self.net.tor_net[0]
        self.dsdb_expect_add("unittest16.aqd-unittest.ms.com", net.usable[2],
                             "eth0", net.usable[2].mac)
        self.noouttest(["add", "host",
                        "--hostname", "unittest16.aqd-unittest.ms.com",
                        "--ipfromip", net.usable[0], "--ipalgorithm", "lowest",
                        "--machine", "ut8s02p2", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--personality", "compileserver"])
        self.dsdb_verify()

    def testverifyunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest16.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[0].usable[2],
                         command)
        self.matchoutput(out, "Personality: compileserver", command)

    #test aquilons default linux/4.0.1-x86_64
    def testaddunittest17(self):
        ip = self.net.tor_net[0].usable[3]
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
                         self.net.tor_net[0].usable[3],
                         command)
        self.matchoutput(out,
                         "Template: aquilon/os/linux/4.0.1-x86_64/config.tpl",
                         command)
        self.matchoutput(out, "Personality: inventory", command)

    def testaddnointerface(self):
        ip = self.net.unknown[0].usable[-1]
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
        servers = 0
        user = self.config.get("unittest", "user")
        net = self.net.tor_net[1]
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
                       "--osname", "linux", "--osversion", "4.0.1-x86_64",
                       "--archetype", "aquilon", "--personality", "inventory"]
            self.noouttest(command)
        self.dsdb_verify()

    def testpopulateverarirackhosts(self):
        # This gives us evh1.aqd-unittest.ms.com through evh10
        # and leaves the other 40 machines for future use.
        net = self.net.tor_net[2]
        for i in range(101, 110):
            port = i - 100
            hostname = "evh%d.aqd-unittest.ms.com" % port
            self.dsdb_expect_add(hostname, net.usable[port], "eth0",
                                 net.usable[port].mac)
            command = ["add", "host", "--hostname", hostname,
                       "--ip", net.usable[port],
                       "--machine", "ut10s04p%d" % port,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "esx_desktop"]
            self.noouttest(command)
        self.dsdb_verify()

    def testpopulate10gigrackhosts(self):
        # Assuming evh11 - evh50 will eventually be claimed above.
        net = self.net.tor_net2[2]
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
                       "--archetype", "vmhost", "--personality", "esx_desktop"]
            self.noouttest(command)
        self.dsdb_verify()

    def testpopulatehaclusterhosts(self):
        utnet = self.net.tor_net2[3]
        npnet = self.net.tor_net2[4]
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
                       "--archetype", "vmhost", "--personality", "esx_desktop"]
            self.noouttest(command)

            hostname = "evh%d.one-nyp.ms.com" % (i + 50)
            machine = "np13s03p%d" % port
            self.dsdb_expect_add(hostname, npnet.usable[port], "eth0",
                                 npnet.usable[port].mac)
            command = ["add", "host", "--hostname", hostname, "--autoip",
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "esx_desktop"]
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
        self.assertEqual(host.ip, str(self.net.tor_net[2].usable[1]))
        self.assertEqual(host.machine.name, "ut10s04p1")
        self.assertEqual(len(host.machine.interfaces), 2)
        for i in host.machine.interfaces:
            if i.device == 'eth0':
                self.assertEqual(i.ip, str(self.net.tor_net[2].usable[1]))
                # We're not using this field anymore...
                self.assertEqual(i.network_id, 0)
            elif i.device == 'eth1':
                self.assertEqual(i.ip, "")
                self.assertEqual(i.network_id, 0)
            else:
                self.fail("Unrecognized interface '%s'" % i.device)

    def testaddhostnousefularchetype(self):
        command = ["add", "host", "--archetype", "pserver",
                   "--hostname", "unittest01.one-nyp.ms.com",
                   "--ip", self.net.unknown[0].usable[10],
                   "--domain", "unittest", "--machine", "ut3c1n4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Can not determine a sensible default OS", command)

    def testaddccisshost(self):
        ip = self.net.unknown[0].usable[18]
        self.dsdb_expect_add("unittest18.aqd-unittest.ms.com", ip, "eth0",
                             ip.mac)
        command = ["add", "host", "--archetype", "aquilon",
                   "--hostname", "unittest18.aqd-unittest.ms.com", "--ip", ip,
                   "--domain", "unittest", "--machine", "ut3c1n8"]
        self.noouttest(command)
        self.dsdb_verify()

    #test aurora and windows defaults now
    def testaddauroradefaultos(self):
        ip = self.net.tor_net[10].usable[-1]
        self.dsdb_expect("show host -host_name test-aurora-default-os")
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
        self.matchoutput(out, "Template: aurora/os/linux/generic/config.tpl",
                         command)

    def testaddwindowsefaultos(self):
        ip = self.net.tor_net[10].usable[-2]
        self.dsdb_expect_add("test-windows-default-os.msad.ms.com", ip,
                             "eth0", self.net.tor_net[0].usable[5].mac)
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
        self.matchoutput(out, "Template: windows/os/windows/generic/config.tpl",
                         command)

    def testverifyhostall(self):
        command = ["show", "host", "--all"]
        out = self.commandtest(command)
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

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
