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
"""Module for testing the make aquilon command."""

import os
import sys
import unittest
import re

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand

# This tests the "make aquilon" command, which has
# the specific feature of auto-binding required services.

class TestMakeAquilon(TestBrokerCommand):

    def testmakeunittest02(self):
        command = ["make", "aquilon",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--os", "linux/4.0.1-x86_64"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service aqd instance ny-prod",
                         command)
        self.matchclean(out, "removing binding", command)

        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "unittest02.one-nyp.ms.com.xml")))

        self.failUnless(os.path.exists(os.path.join(
            self.config.get("broker", "builddir"),
            "domains", "unittest", "profiles",
            "unittest02.one-nyp.ms.com.tpl")))

        servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                  "servicedata")
        results = self.grepcommand(["-rl", "unittest02.one-nyp.ms.com",
                                    servicedir])
        self.failUnless(results, "No service plenary data that includes"
                                 "unittest02.one-nyp.ms.com")

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c5n10');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip0, self.netmask0, self.broadcast0, self.gateway0),
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/compileserver/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)

    def testmakeunittest00(self):
        command = ["make", "aquilon",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--buildstatus", "blind", "--personality", "compileserver",
                   "--os", "linux/4.0.1-x86_64"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service aqd instance ny-prod",
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service dns instance nyinfratest",
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service afs instance q.ny.ms.com",
                         command)
        self.matchclean(out, "removing binding", command)
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "unittest00.one-nyp.ms.com.xml")))

    def testverifybuildstatus(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: blind", command)

    def testverifybindautoafs(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testverifybindautodns(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/nyinfratest", command)

    def testverifyproto(self):
        command = ["show", "host", "--hostname=unittest00.one-nyp.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.failUnlessEqual(host.hostname, 'unittest00')
        self.failUnlessEqual(host.personality.name, 'compileserver')
        self.failUnlessEqual(host.fqdn, 'unittest00.one-nyp.ms.com')
        self.failUnlessEqual(host.mac, self.hostmac2)
        self.failUnlessEqual(host.ip, self.hostip2)
        self.failUnlessEqual(host.archetype.name, 'aquilon')
        self.failUnlessEqual(host.dns_domain, 'one-nyp.ms.com')
        self.failUnlessEqual(host.domain.name, 'unittest')
        self.failUnlessEqual(host.status, 'blind')
        self.failUnlessEqual(host.machine.name, 'ut3c1n3')
        self.failUnlessEqual(host.sysloc, 'ut.ny.na')
        self.failUnlessEqual(host.type, 'host')
        self.failUnlessEqual(host.personality.name, 'compileserver')
        self.failUnlessEqual(host.personality.archetype.name, 'aquilon')

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c1n3');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip2, self.netmask2, self.broadcast2, self.gateway2),
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth1' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip3, self.netmask3, self.broadcast3, self.gateway3),
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/compileserver/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)

    def testverifyshowservicebyclient(self):
        command = "show service --client unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)
        self.matchoutput(out, "Service: dns Instance: nyinfratest", command)
        self.matchoutput(out, "Service: ntp Instance: pa.ny.na", command)

    def testmakehpinventory(self):
        # Expand this as necessary... keep in mind that range() is
        # inclusive for the first argument and exclusive on the second.
        # So for 51-60 use range(51, 61)
        # 51 - 60 are server(1-10).aqd-unittest.ms.com
        # 61 - 65 are taken here
        # 66 - 70 are RHEL 5 below
        # 71 - 80 UNUSED
        # 81 - 90 are unixeng-test below
        # 91 - 99 are reserved for testing failure conditions
        for i in range(61, 66):
            hostname = "aquilon%d.aqd-unittest.ms.com" % i
            command = ["make", "aquilon", "--hostname", hostname,
                       "--os", "linux/4.0.1-x86_64"]
            out = self.commandtest(command)
            self.matchoutput(out, "%s adding binding" % hostname, command)
            self.matchclean(out, "removing binding", command)

    def testmakerhel5(self):
        for i in range(66, 71):
            hostname = "aquilon%d.aqd-unittest.ms.com" % i
            command = ["make", "aquilon", "--hostname", hostname,
                       "--os", "linux/5.0-x86_64"]
            out = self.commandtest(command)
            self.matchoutput(out, "%s adding binding" % hostname, command)
            self.matchclean(out, "removing binding", command)

    def testmakehpunixeng(self):
        for i in range(81, 91):
            hostname = "aquilon%d.aqd-unittest.ms.com" % i
            command = ["make", "aquilon", "--hostname", hostname,
                       "--personality", "unixeng-test",
                       "--os", "linux/4.0.1-x86_64"]
            out = self.commandtest(command)
            self.matchoutput(out, "%s adding binding" % hostname, command)
            self.matchoutput(out, "service chooser1", command)
            self.matchoutput(out, "service chooser2", command)
            self.matchoutput(out, "service chooser3", command)
            self.matchclean(out, "removing binding", command)

    def testmissingrequiredservice(self):
        command = ["make", "aquilon",
                   "--hostname", "aquilon91.aqd-unittest.ms.com",
                   "--personality", "badpersonality2",
                   "--os", "linux/4.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not find a relevant service map", command)

    def testmissingrequiredservicedebug(self):
        command = ["make", "aquilon", "--debug",
                   "--hostname", "aquilon92.aqd-unittest.ms.com",
                   "--personality", "badpersonality2",
                   "--os", "linux/4.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Creating service Chooser", command)
        self.matchoutput(out, "Could not find a relevant service map", command)

    def testmissingpersonalitytemplate(self):
        command = ["make", "aquilon",
                   "--hostname", "aquilon93.aqd-unittest.ms.com",
                   "--personality", "badpersonality",
                   "--os", "linux/4.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot locate template", command)
        self.failIf(os.path.exists(os.path.join(
            self.config.get("broker", "builddir"),
            "domains", "unittest", "profiles",
            "aquilon93.aqd-unittest.ms.com.tpl")))
        servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                  "servicedata")
        results = self.grepcommand(["-rl", "aquilon93.aqd-unittest.ms.com",
                                    servicedir])
        self.failIf(results, "Found service plenary data that includes "
                             "aquilon93.aqd-unittest.ms.com")

    def testfailwindows(self):
        command = ["make", "aquilon",
                   "--hostname", "unittest01.one-nyp.ms.com",
                   "--os", "linux/4.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is not a compilable archetype", command)

    # Turns out this test is completely bogus.  There is a sequence of
    # binding that would allow a client to bind to ut.a on chooser1
    # without needing to be bound to ut.a on chooser2 or chooser3.  The
    # problem is that the sequence of binding to services is random.
    # If chooser1 was always bound first (as I originally assumed it
    # wuld work out), any time it had ut.a chooser2 and chooser3 would
    # as well.
   #def testverifyaffinityalgorithm(self):
   #    # To a large extent, this test is bogus... this was more
   #    # thoroughly checked by hand and with the coverage module.
   #    command = ["search_host", "--service=chooser1", "--instance=ut.a"]
   #    chooser1_uta = self.commandtest(command).splitlines()
   #    command = ["search_host", "--service=chooser2", "--instance=ut.a"]
   #    chooser2_uta = self.commandtest(command).splitlines()
   #    command = ["search_host", "--service=chooser3", "--instance=ut.a"]
   #    chooser3_uta = self.commandtest(command).splitlines()
   #    self.failUnless(chooser1_uta,
   #                    "Expected host list, got '%s'" % chooser1_uta)
   #    # 2 and 3 will have extra entries...
   #    # Ideally they wouldn't (choosing them would force the algorithm
   #    # to go back and choose ut.a for chooser1), but the code is not
   #    # that sophisticated.
   #    for host in chooser1_uta:
   #        self.failUnless(host in chooser2_uta,
   #                        "Host %s not in %s" % (host, chooser2_uta))
   #        self.failUnless(host in chooser3_uta,
   #                        "Host %s not in %s" % (host, chooser3_uta))

    def testverifyleastloadalgorithm(self):
        # This is bogus too... again checked more manually with
        # coverage and --debug then with this.
        # Basically, the count skews towards ut.a because of server
        # affinity, and then least load kicks in to distribute
        # relatively evenly between ut.b and ut.c.
        count_re = re.compile(r'\s*Client Count: (\d+)')
        command = "show_service --service=chooser1"
        out = self.commandtest(command.split(" "))
        counts = [int(c) for c in count_re.findall(out)]
        self.failUnless(len(counts) > 2,
                        "Not enough client counts in output '%s'" % out)
        # This test is too non-deterministic, and fails randomly.
        # Until there's something better, the final does-each-instance-
        # at-least-have-one?-test will have to suffice.
        #counts.sort()
        #self.failUnless(abs(counts[0]-counts[1]) <= 1,
        #                "Client counts vary by more than 1 %s" % counts)
        self.failIf(counts[0] < 1,
                    "One of the instances was never bound:\n%s" % out)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeAquilon)
    unittest.TextTestRunner(verbosity=2).run(suite)
