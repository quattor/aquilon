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
"""Module for testing the reconfigure command."""


import os
import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestReconfigure(TestBrokerCommand):
    # Note that some tests for reconfigure --list appear in
    # test_make_aquilon.py.

    # The unbind test has removed the service bindings for dns,
    # it should now be set again.
    # The rebind test has changed the service bindings for afs,
    # it should now be set to q.ln.ms.com.  The reconfigure will
    # force it *back* to using a correct service map entry, in
    # this case q.ny.ms.com.
    def testreconfigureunittest02_1(self):
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
        self.matchoutput(err, "sent 1 server notifications", command)

    ## verify status before reconfigure
    def testreconfigureunittest02_0(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))

    def testverifybuildstatus(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: ready", command)
        self.matchoutput(out, "Advertise Status: true", command)

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create("machine/americas/ut/ut3/ut3c5n10");""",
            command)
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest02.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\)' %
                          (self.net.unknown[0].broadcast,
                           self.net.unknown[0].gateway,
                           self.net.unknown[0].usable[0],
                           self.net.unknown[0].netmask),
                          command)
        self.matchoutput(out,
            """include { "archetype/base" };""",
            command)
        self.matchoutput(out,
            """include { "os/linux/5.0.1-x86_64/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/afs/q.ny.ms.com/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/bootserver/np.test/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/dns/utdnsinstance/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/ntp/pa.ny.na/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "personality/compileserver/config" };""",
            command)
        self.matchoutput(out,
            """include { "archetype/final" };""",
            command)
        self.matchoutput(out, "'/system/advertise_status' = true;", command)

    # These settings have not changed - the command should still succeed.
    def testreconfigureunittest00(self):
        command = ["reconfigure", "--hostname", "unittest00.one-nyp.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "0/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)
        self.matchoutput(err, "sent 1 server notifications", command)

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create("machine/americas/ut/ut3/ut3c1n3");""",
            command)
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest00.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\),' %
                          (self.net.unknown[0].broadcast,
                           self.net.unknown[0].gateway,
                           self.net.unknown[0].usable[2],
                           self.net.unknown[0].netmask),
                          command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest00-e1.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\)\s*\);' %
                          (self.net.unknown[0].broadcast,
                           self.net.unknown[0].gateway,
                           self.net.unknown[0].usable[3],
                           self.net.unknown[0].netmask),
                          command)
        self.matchoutput(out,
            """include { "archetype/base" };""",
            command)
        self.matchoutput(out,
            """include { "os/linux/5.0.1-x86_64/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/afs/q.ny.ms.com/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/bootserver/np.test/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/dns/utdnsinstance/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/ntp/pa.ny.na/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "personality/compileserver/config" };""",
            command)
        self.matchoutput(out,
            """include { "archetype/final" };""",
            command)
        self.matchoutput(out, "'/system/advertise_status' = false;", command)

    def testreconfigurewindowsstatus(self):
        self.noouttest(["reconfigure",
                        "--hostname", "unittest01.one-nyp.ms.com",
                        "--buildstatus", "ready"])

    def testreconfigurewindowspersonality(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--personality", "desktop"]
        self.noouttest(command)

    def testreconfigurewindowsos(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--osversion", "nt61e"]
        self.noouttest(command)

    def testreconfigurewindowswrongos(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--os", "linux/5.0.1-x86_64"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Operating System linux, version 5.0.1-x86_64, "
                         "archetype windows not found.",
                         command)

    def testreconfigurewindowswrongarch(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--archetype", "aquilon", "--personality", "unixeng-test"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Operating System windows/windows-nt61e belongs to "
                         "archetype windows, not archetype aquilon.  Please "
                         "specify --osname/--osversion.",
                         command)

    def testreconfigurewindowswrongarchlist(self):
        hosts = ["unittest01.one-nyp.ms.com\n"]
        scratchfile = self.writescratch("hostlist", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype", "aquilon", "--personality=unixeng-test"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "unittest01.one-nyp.ms.com: Cannot change archetype "
                         "because operating system windows/windows-nt61e needs "
                         "archetype windows.",
                         command)

    def testverifyreconfigurewindows(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: desktop", command)
        self.matchoutput(out, "Build Status: ready", command)
        self.matchoutput(out, "Operating System: windows", command)
        self.matchoutput(out, "Version: nt61e", command)
        self.matchoutput(out, "Advertise Status: true", command)

    def testreconfigureos(self):
        command = ["reconfigure",
                   "--hostname", "aquilon61.aqd-unittest.ms.com",
                   "--os", "linux/5.0-x86_64"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def testreconfigureossplitargs(self):
        command = ["reconfigure",
                   "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--osname", "linux", "--osversion", "5.0-x86_64"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def testmissingpersonalitytemplate(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot locate template", command)
        buildfile = os.path.join(self.config.get("broker", "builddir"),
                                 "domains", "utsandbox", "profiles",
                                 "aquilon62.aqd-unittest.ms.com.tpl")
        results = self.grepcommand(["-l", "badpersonality", buildfile])
        self.failIf(results, "Found bad personality data in plenary "
                             "template for aquilon62.aqd-unittest.ms.com")

    def testmissingpersonalitytemplatehostlist(self):
        hosts = ["aquilon93.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("missingtemplate", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype", "aquilon", "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot locate template", command)
        self.failIf(os.path.exists(os.path.join(
            self.config.get("broker", "builddir"),
            "domains", "utsandbox", "profiles",
            "aquilon93.aqd-unittest.ms.com.tpl")))
        servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                  "servicedata")
        results = self.grepcommand(["-rl", "aquilon93.aqd-unittest.ms.com",
                                    servicedir])
        self.failIf(results, "Found service plenary data that includes "
                             "aquilon93.aqd-unittest.ms.com")

    def testmissingpersonality(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--archetype", "windows"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Changing archetype also requires "
                         "specifying --personality.",
                         command)

    def testmissingrequiredservice(self):
        hosts = ["aquilon91.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("missingmap", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype", "aquilon",
                   "--personality", "badpersonality2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not find a relevant service map", command)
        self.matchoutput(out, "The following hosts failed service binding:",
                         command)
        self.matchoutput(out, "aquilon91.aqd-unittest.ms.com", command)

    def testkeepbindings(self):
        command = ["reconfigure", "--keepbindings",
                   "--hostname", "aquilon86.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
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
            """'/hardware' = create("machine/americas/ut/ut9/ut9s03p37");""",
            command)
        self.matchoutput(out,
            """include { "archetype/base" };""",
            command)
        self.matchoutput(out,
            """include { "os/linux/5.0.1-x86_64/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/aqd/ny-prod/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/ntp/pa.ny.na/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/bootserver/np.test/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/afs/q.ny.ms.com/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/dns/utdnsinstance/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "personality/inventory/config" };""",
            command)
        self.matchoutput(out,
            """include { "archetype/final" };""",
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

    def testfailpersonalitynotallowed(self):
        command = ["reconfigure", "--hostname=evh2.aqd-unittest.ms.com",
                   "--personality=esx_server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The personality vmhost/esx_server is not allowed by "
                         "ESX Cluster utecl1.  Specify one of "
                         "['vmhost/esx_desktop'].",
                         command)

    def testfailpersonalitynotallowedlist(self):
        hosts = ["evh2.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("persnotallowed", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype=vmhost", "--personality=esx_server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "evh2.aqd-unittest.ms.com: The personality "
                         "vmhost/esx_server is not allowed by ESX Cluster "
                         "utecl1.  Specify one of ['vmhost/esx_desktop'].",
                         command)

    def testverifyalignedservice(self):
        # Check that utecl1 is now aligned to a service and that
        # all of its members are aligned to the same service.
        # evh[234] should be bound to utecl1
        command = "show esx cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        m = re.search(r'Member Alignment: Service esx_management_server '
                       'Instance (\S+)', out)
        self.failUnless(m, "Aligned instance not found in output:\n%s" % out)
        instance = m.group(1)
        # A better test might be to search for all hosts in the cluster
        # and make sure they're all in this list.  That search command
        # does not exist yet, though.
        command = ["search_host", "--service=esx_management_server",
                   "--instance=%s" % instance]
        out = self.commandtest(command)
        self.matchoutput(out, "evh2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh4.aqd-unittest.ms.com", command)

    # This doesn't work since the manage test comes after this one.
    # Note that these are template domains and not dns domains.
#   def testhostlistdomains(self):
#       hosts = ["unittest02.one-nyp.ms.com\n",
#                "aquilon91.aqd-unittest.ms.com\n"]
#       scratchfile = self.writescratch("diffdomains", "".join(hosts))
#       command = ["reconfigure", "--list", scratchfile]
#       out = self.badrequesttest(command)
#       self.matchoutput(out, "All hosts must be in the same domain:", command)
#       self.matchoutput(out, "1 hosts in domain changetest1", command)
#       self.matchoutput(out, "1 hosts in domain unittest", command)

    def testhostlistos(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("bados", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--os=os-does-not-exist"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Please use --osname and --osversion to "
                         "specify a new OS.",
                         command)

    def testhostlistnoosversion(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingosversion", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile, "--osname=linux"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Please specify --osversion for OS linux",
                         command)

    def testhostlistnoosname(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingosname", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--osversion=5.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Please specify --osname to use with "
                         "OS version 5.0.1-x86_64",
                         command)

    def testhostlistnoosarchetype(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingosarchetype", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--osname=linux", "--osversion=5.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Please specify --archetype for OS "
                         "linux, version 5.0.1-x86_64",
                         command)

    def testhostlistpersonalitynoarchetype(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingarchetype", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--personality=generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality generic is not unique.", command)

    def testemptyhostlist(self):
        hosts = ["#host\n", "#does\n", "\n", "   #not   \n", "#exist\n"]
        scratchfile = self.writescratch("empty", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Empty hostlist.", command)

    def testemptyhostlist(self):
        hosts = ["host-does-not-exist.aqd-unittest.ms.com\n",
                 "another-host-does-not-exist.aqd-unittest.ms.com\n",
                 "aquilon91.aqd-unittest.ms.com\n",
                 "host.domain-does-not-exist.ms.com\n"]
        scratchfile = self.writescratch("missinghost", "".join(hosts))
        # Use the deprecated option name here
        command = ["reconfigure", "--hostlist", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid hosts in list:", command)
        self.matchoutput(out, "host-does-not-exist.aqd-unittest.ms.com:",
                         command)
        self.matchoutput(out,
                         "another-host-does-not-exist.aqd-unittest.ms.com:",
                         command)
        self.matchoutput(out, "host.domain-does-not-exist.ms.com:", command)
        self.matchclean(out, "aquilon91.aqd-unittest.ms.com:", command)

    # Need easy ordering for these, so using numbers...
    # If we end up fixing map dns domain, it may be harder to do this test.
    # Also, these tests would just "keep working", but they wouldn't
    # actually be testing anything...
    def test_100_reconfigure_aquilon95(self):
        command = ["reconfigure", "--hostname=aquilon95.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_110_map_dns_domain(self):
        out = self.successtest(['map_dns_domain', '--building=ut',
                                '--dns_domain=aqd-unittest.ms.com'])

    def test_120_reconfigure_aquilon95(self):
        command = ["reconfigure", "--hostname=aquilon95.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)

    def test_130_verify_machine_plenary(self):
        command = ["cat", "--machine=ut9s03p45"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = '
                          r'list\(\s*"aqd-unittest.ms.com",\s*'
                          r'"new-york.ms.com"\s*\);',
                          command)

    def test_140_unmap_dns_domain(self):
        out = self.successtest(['unmap_dns_domain', '--building=ut',
                                '--dns_domain=aqd-unittest.ms.com'])

    def test_150_reconfigure_aquilon95(self):
        command = ["reconfigure", "--hostname=aquilon95.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)

    def test_160_verify_machine_plenary(self):
        command = ["cat", "--machine=ut9s03p45"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = '
                          r'list\(\s*"new-york.ms.com"\s*\);',
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReconfigure)
    unittest.TextTestRunner(verbosity=2).run(suite)
