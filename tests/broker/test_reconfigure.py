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
"""Module for testing the reconfigure command."""

import os
import sys
import unittest
import re

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestReconfigure(TestBrokerCommand):

    # The unbind test has removed the service bindings for dns,
    # it should now be set again.
    # The rebind test has changed the service bindings for afs,
    # it should now be set to q.ln.ms.com.  The reconfigure will
    # force it *back* to using a correct service map entry, in
    # this case q.ny.ms.com.
    def testreconfigureunittest02(self):
        command = ["reconfigure", "--hostname", "unittest02.one-nyp.ms.com",
                   "--buildstatus", "ready"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service afs instance q.ny.ms.com",
                         command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com removing binding for "
                         "service afs instance q.ln.ms.com",
                         command)

    def testverifybuildstatus(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: ready", command)

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c5n10');""",
            command)
        self.matchoutput(out,
                         "'/system/network/interfaces/eth0' = "
                         "nlist('ip', '%s', 'netmask', '%s', "
                         "'broadcast', '%s', 'gateway', '%s', "
                         "'bootproto', 'static');" %
                         (self.net.unknown[0].usable[0].ip,
                          self.net.unknown[0].netmask,
                          self.net.unknown[0].broadcast,
                          self.net.unknown[0].gateway),
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

    # These settings have not changed - the command should still succeed.
    def testreconfigureunittest00(self):
        command = ["reconfigure", "--hostname", "unittest00.one-nyp.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "0/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c1n3');""",
            command)
        self.matchoutput(out,
                         "'/system/network/interfaces/eth0' = "
                         "nlist('ip', '%s', 'netmask', '%s', "
                         "'broadcast', '%s', 'gateway', '%s', "
                         "'bootproto', 'static');" %
                         (self.net.unknown[0].usable[2].ip,
                          self.net.unknown[0].netmask,
                          self.net.unknown[0].broadcast,
                          self.net.unknown[0].gateway),
                         command)
        self.matchoutput(out,
                         "'/system/network/interfaces/eth1' = "
                         "nlist('ip', '%s', 'netmask', '%s', "
                         "'broadcast', '%s', 'gateway', '%s', "
                         "'bootproto', 'static');" %
                         (self.net.unknown[0].usable[3].ip,
                          self.net.unknown[0].netmask,
                          self.net.unknown[0].broadcast,
                          self.net.unknown[0].gateway),
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

    def testreconfigurewindowsstatus(self):
        self.noouttest(["reconfigure",
                        "--hostname", "unittest01.one-nyp.ms.com",
                        "--buildstatus", "ready"])

    def testreconfigurewindowsmissingargs(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Nothing to do.", command)

    def testreconfigurewindowspersonality(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--personality", "desktop"]
        self.noouttest(command)

    def testreconfigurewindowsos(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--os", "linux/4.0.1-x86_64"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Can only set os for compileable archetypes",
                         command)

    def testverifyreconfigurewindows(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: desktop", command)
        self.matchoutput(out, "Build Status: ready", command)

    def testreconfigureos(self):
        command = ["reconfigure",
                   "--hostname", "aquilon61.aqd-unittest.ms.com",
                   "--os", "linux/5.0-x86_64"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def testmissingpersonalitytemplate(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot locate template", command)
        buildfile = os.path.join(self.config.get("broker", "builddir"),
                                 "domains", "unittest", "profiles",
                                 "aquilon62.aqd-unittest.ms.com.tpl")
        results = self.grepcommand(["-l", "badpersonality", buildfile])
        self.failIf(results, "Found bad personality data in plenary "
                             "template for aquilon62.aqd-unittest.ms.com")

    def testmissingpersonality(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--archetype", "windows"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Changing archetype also requires "
                         "specifying personality.",
                         command)

    def testkeepbindings(self):
        command = ["reconfigure", "--keepbindings",
                   "--hostname", "aquilon86.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def verifykeepbindings(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["search_host", "--service", service,
                       "--hostname", "aquilon86.aqd-unittest.ms.com",
                       "--archetype", "aquilon", "--personality", "inventory"]
            out = self.commandtest(command)
            self.matchoutput(out, "aquilon86.aqd-unittest.ms.com")

    def testremovebindings(self):
        command = ["reconfigure",
                   "--hostname", "aquilon87.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "removing binding for service chooser1", command)
        self.matchoutput(err, "removing binding for service chooser2", command)
        self.matchoutput(err, "removing binding for service chooser3", command)
        self.matchclean(err, "adding binding", command)

    def testverifyremovebindings(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["search_host", "--service", service,
                       "--hostname", "aquilon87.aqd-unittest.ms.com"]
            self.noouttest(command)

    def testverifyremovebindingscat(self):
        command = "cat --hostname aquilon87.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "chooser1", command)
        self.matchclean(out, "chooser2", command)
        self.matchclean(out, "chooser3", command)
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut9/ut9s03p37');""",
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/aqd/ny-prod/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/inventory/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)

    def testreconfiguredebug(self):
        command = ["reconfigure", "--debug",
                   "--hostname", "aquilon88.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Creating service Chooser", command)

    def testreconfigureboundvmhosts(self):
        # This will exercise the cluster-aligned services code,
        # which does not kick in at 'make' time because the hosts
        # have not been bound to clusters yet.
        for i in range(1, 5):
            command = ["reconfigure",
                       "--hostname", "evh%s.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)

    def testverifyalignedservice(self):
        # Check that utecl1 is now aligned to a service and that
        # all of its members are aligned to the same service.
        # evh[234] should be bound to utecl1
        command = "show esx cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        m = re.search(r'Member Alignment: Service esx_management '
                       'Instance (\S+)', out)
        self.failUnless(m, "Aligned instance not found in output:\n%s" % out)
        instance = m.group(1)
        # A better test might be to search for all hosts in the cluster
        # and make sure they're all in this list.  That search command
        # does not exist yet, though.
        command = ["search_host", "--service=esx_management",
                   "--instance=%s" % instance]
        out = self.commandtest(command)
        self.matchoutput(out, "evh2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh4.aqd-unittest.ms.com", command)

    def testreconfigureunboundvmhosts(self):
        # None of these should change since they have not been bound.
        # This test isn't really necessary...
        for i in range(6, 10):
            command = ["reconfigure",
                       "--hostname", "evh%s.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)
            self.matchoutput(out, "0/1 object template", command)
            self.matchclean(err, "removing binding", command)
            self.matchclean(err, "adding binding", command)

    def testfailchangeclustermemberpersonality(self):
        command = ["reconfigure", "--hostname", "evh1.aqd-unittest.ms.com",
                   "--archetype", "aquilon", "--personality", "inventory"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot change personality of host "
                         "evh1.aqd-unittest.ms.com while it is a member of "
                         "esx cluster ",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReconfigure)
    unittest.TextTestRunner(verbosity=2).run(suite)

