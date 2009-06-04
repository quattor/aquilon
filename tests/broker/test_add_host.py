#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
                        "--ip", self.hostip0,
                        "--machine", "ut3c5n10", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--personality", "compileserver"])

    def testverifyaddunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip0, command)
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
            "--machine", "ut8s02p1", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])

    def testverifyunittest15(self):
        command = "show host --hostname unittest15.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest15.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.hostip15, command)
        self.matchoutput(out, "Personality: inventory", command)

    def testaddunittest16bad(self):
        command = ["add", "host",
                   "--hostname", "unittest16.aqd-unittest.ms.com",
                   "--ipfromip", self.hostip14,
                   "--ipalgorithm", "max",
                   "--machine", "ut8s02p2", "--domain", "unittest",
                   "--buildstatus", "build", "--archetype", "aquilon",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No remaining IPs found on network", command)

    def testaddunittest16good(self):
        self.noouttest(["add", "host",
                        "--hostname", "unittest16.aqd-unittest.ms.com",
                        "--ipfromip", self.hostip14,
                        "--ipalgorithm", "lowest",
                        "--machine", "ut8s02p2", "--domain", "unittest",
                        "--buildstatus", "build", "--archetype", "aquilon",
                        "--personality", "compileserver"])

    def testverifyunittest16(self):
        command = "show host --hostname unittest16.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest16.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.hostip16, command)
        self.matchoutput(out, "Personality: compileserver", command)

    def testaddunittest17(self):
        self.noouttest(["add", "host",
            "--hostname", "unittest17.aqd-unittest.ms.com",
            "--ipfromsystem", "ut01ga1s02.aqd-unittest.ms.com",
            "--machine", "ut8s02p3", "--domain", "unittest",
            "--buildstatus", "build", "--archetype", "aquilon"])

    def testverifyunittest17(self):
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest17.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.hostip17, command)
        self.matchoutput(out, "Personality: inventory", command)

    def testpopulatehprackhosts(self):
        # This gives us server1.aqd-unittest.ms.com through server10
        # and aquilon60.aqd-unittest.ms.com through aquilon100
        # It also needs to run *after* the testadd* methods above
        # as some of them rely on a clean IP space for testing the
        # auto-allocation algorithms.
        servers = 0
        for i in range(51, 100):
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            port = i - 50
            hostip = getattr(self, "hostip%d" % i)
            command = ["add", "host", "--hostname", hostname,
                       "--ipfromip", hostip, "--machine", "ut9s03p%d" % port,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--archetype", "aquilon", "--personality", "inventory"]
            self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
