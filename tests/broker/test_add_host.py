#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddHost(TestBrokerCommand):

    def testaddunittest02(self):
        self.noouttest(["add", "host",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--ip", self.net.unknown[0].usable[0].ip,
                        "--machine", "ut3c5n10", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--personality", "compileserver"])

    def testverifyaddunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[0].ip,
                         command)
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Personality: compileserver", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: build", command)

    def testreconfigurefails(self):
        command = ["reconfigure", "--hostname", "unittest02.one-nyp.ms.com"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "host unittest02.one-nyp.ms.com has not been built",
                         command)

    def testverifyshowfqdnhost(self):
        command = "show fqdn --fqdn unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)

    def testshowhostbaddomain(self):
        command = "show host --hostname aquilon00.one-nyp"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                "DNS domain 'one-nyp' for 'aquilon00.one-nyp' not found",
                command)

    def testverifyunittest02proto(self):
        command = "show host --hostname unittest02.one-nyp.ms.com --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_hostlist_msg(out)

    def testaddunittest15(self):
        self.noouttest(["add", "host",
            "--hostname", "unittest15.aqd-unittest.ms.com",
            "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
            "--ipalgorithm", "max",
            "--osname", "linux", "--osversion", "4.0.1-x86_64",
            "--machine", "ut8s02p1", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])

    def testverifyunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest15.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.tor_net[0].usable[1].ip,
                         command)
        self.matchoutput(out, "Personality: inventory", command)

    def testaddunittest16bad(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", self.net.tor_net2[1].usable[-1].ip,
                   "--ipalgorithm", "max",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--osname", "linux", "--osversion", "4.0.1-x86_64",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No remaining IPs found on network", command)

    def testaddunittest16good(self):
        self.noouttest(["add", "host",
                        "--hostname", "unittest16.aqd-unittest.ms.com",
                        "--ipfromip", self.net.tor_net[0].usable[0].ip,
                        "--ipalgorithm", "lowest",
                        "--machine", "ut8s02p2", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--personality", "compileserver"])

    def testverifyunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest16.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.tor_net[0].usable[2].ip,
                         command)
        self.matchoutput(out, "Personality: compileserver", command)

    #test aquilons default linux/4.0.1-x86_64
    def testaddunittest17(self):
        self.noouttest(["add", "host",
            "--hostname", "unittest17.aqd-unittest.ms.com",
            "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
            "--machine", "ut8s02p3", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])

    def testverifyunittest17(self):
        #verifies default os and personality for aquilon
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest17.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.tor_net[0].usable[3].ip,
                         command)
        self.matchoutput(out,
                         "Template: aquilon/os/linux/4.0.1-x86_64/config.tpl",
                         command)
        self.matchoutput(out, "Personality: inventory", command)

    def testpopulatehprackhosts(self):
        # This gives us server1.aqd-unittest.ms.com through server10
        # and aquilon60.aqd-unittest.ms.com through aquilon100
        # It also needs to run *after* the testadd* methods above
        # as some of them rely on a clean IP space for testing the
        # auto-allocation algorithms.
        # I stole the last 2 hp rack hosts for default host
        servers = 0
        for i in range(51, 100):
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            port = i - 50
            command = ["add", "host", "--hostname", hostname,
                       "--ip", self.net.tor_net[1].usable[port].ip,
                       "--machine", "ut9s03p%d" % port,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "linux", "--osversion", "4.0.1-x86_64",
                       "--archetype", "aquilon", "--personality", "inventory"]
            self.noouttest(command)

    def testpopulateverarirackhosts(self):
        # This gives us evh1.aqd-unittest.ms.com through evh10
        # and leaves the other 40 machines for future use.
        for i in range(101, 110):
            port = i - 100
            hostname = "evh%d.aqd-unittest.ms.com" % port
            command = ["add", "host", "--hostname", hostname,
                       "--ip", self.net.tor_net[2].usable[port].ip,
                       "--machine", "ut10s04p%d" % port,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "4.0.0",
                       "--archetype", "vmhost", "--personality", "esx_server"]
            self.noouttest(command)

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
        self.assertEqual(host.ip, self.net.tor_net[2].usable[1].ip)
        self.assertEqual(host.machine.name, "ut10s04p1")
        self.assertEqual(len(host.machine.interfaces), 2)
        for i in host.machine.interfaces:
            if i.device == 'eth0':
                self.assertEqual(i.ip, self.net.tor_net[2].usable[1].ip)
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
                   "--ip", self.net.unknown[0].usable[10].ip,
                   "--domain", "unittest", "--machine", "ut3c1n4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Can not determine a sensible default OS", command)

    #test aurora and windows defaults now
    def testaddauroradefaultos(self):
        self.noouttest(["add", "host", "--archetype", "aurora",
                        "--hostname", "test_aurora_default_os.ms.com",
                        "--ip", "4.2.3.126", "--domain", "ny-prod", "--machine",
                        "ut8s02p4"])

    def testverifyaddauroradefaultos(self):
        command = "show host --hostname test_aurora_default_os.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: test_aurora_default_os.ms.com", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Template: aurora/os/linux/generic/config.tpl",
                         command)

    def testaddwindowsefaultos(self):
        self.noouttest(["add", "host", "--archetype", "windows",
                        "--hostname", "test_windows_default_os.msad.ms.com",
                        "--ip", "4.2.3.127", "--domain", "ny-prod",
                        "--machine", "ut8s02p5"])

    def testverifyaddwindowsdefaultos(self):
        command = "show host --hostname test_windows_default_os.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: test_windows_default_os.msad.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Template: windows/os/windows/generic/config.tpl",
                         command)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
