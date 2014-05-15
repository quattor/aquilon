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
"""Module for testing the make aquilon command."""

import os
import re
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestMakeAquilon(VerifyNotificationsMixin, TestBrokerCommand):
    """ This tests the "make aquilon" command

        which has the specific feature of auto-binding required services
    """

    def testmakeinfra(self):
        command = ["make", "--hostname", "infra1.one-nyp.ms.com"]
        self.statustest(command)
        command = ["make", "--hostname", "infra1.aqd-unittest.ms.com"]
        self.statustest(command)

    def testmakeunittest02(self):
        basetime = datetime.now()
        command = ["make", "aquilon",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance aqd/ny-prod",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

        self.verify_buildfiles("unittest", "unittest02.one-nyp.ms.com",
                               command="make_aquilon")

        # The .dep file should not get copied into the web directory
        profilesdir = self.config.get("broker", "profilesdir")
        self.failIf(os.path.exists(os.path.join(profilesdir,
                                                "unittest02.one-nyp.ms.com.dep")))

        servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                  "servicedata")
        results = self.grepcommand(["-rl", "unittest02.one-nyp.ms.com",
                                    servicedir])
        self.failUnless(results, "No service plenary data that includes"
                                 "unittest02.one-nyp.ms.com")

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         '"hardware" = create("machine/americas/ut/ut3/ut3c5n10");',
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
                          r'"network_type", "unknown"\s*\)\s*' %
                          (self.net["unknown0"].broadcast,
                           self.net["unknown0"].gateway,
                           self.net["unknown0"].usable[0],
                           self.net["unknown0"].netmask),
                          command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"bootproto", "none"\s*\)',
                          command)
        self.searchoutput(out,
                          r'"eth1\.2", nlist\(\s*'
                          r'"bootproto", "none",\s*'
                          r'"physdev", "eth1",\s*'
                          r'"vlan", true\s*\)',
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = "%s";' %
                         self.net["unknown0"].gateway, command)
        self.matchoutput(out, '"system/advertise_status" = false', command)

        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))

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
                         """include { "service/bootserver/unittest/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "service/dns/unittest/client/config" };""",
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

        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)
        self.matchclean(out, '"/metadata/template/branch/author"', command)

    def testverifyunittest02services(self):
        for service, instance in [("afs", "q.ny.ms.com"),
                                  ("bootserver", "unittest"),
                                  ("dns", "unittest"),
                                  ("ntp", "pa.ny.na"),
                                  ("support-group", "ec-service")]:
            command = ["cat", "--service", service, "--instance", instance,
                       "--server"]
            out = self.commandtest(command)
            self.searchoutput(out,
                              r'"clients" = list\(([^)]|\s)*"unittest02.one-nyp.ms.com"',
                              command)

    def testmakeunittest00(self):
        basetime = datetime.now()
        command = ["make", "aquilon",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--buildstatus", "blind", "--personality", "compileserver",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service instance aqd/ny-prod",
                         command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service instance dns/unittest",
                         command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service instance afs/q.ny.ms.com",
                         command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "unittest00.one-nyp.ms.com%s" % self.xml_suffix)))

    def testverifybuildstatus(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: blind", command)
        self.matchoutput(out, "Advertise Status: False", command)

    def testverifybindautoafs(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: afs Instance: q.ny.ms.com",
                         command)

    def testverifybindautodns(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: dns Instance: unittest",
                         command)

    def testverifyproto(self):
        command = ["show", "host", "--hostname=unittest00.one-nyp.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.failUnlessEqual(host.hostname, 'unittest00')
        self.failUnlessEqual(host.personality.name, 'compileserver')
        self.failUnlessEqual(host.fqdn, 'unittest00.one-nyp.ms.com')
        self.failUnlessEqual(host.mac, self.net["unknown0"].usable[2].mac)
        self.failUnlessEqual(host.ip, str(self.net["unknown0"].usable[2]))
        self.failUnlessEqual(host.archetype.name, 'aquilon')
        self.failUnlessEqual(host.dns_domain, 'one-nyp.ms.com')
        self.failUnlessEqual(host.domain.name, 'unittest')
        self.failUnlessEqual(host.status, 'blind')
        self.failUnlessEqual(host.machine.name, 'ut3c1n3')
        self.failUnlessEqual(host.sysloc, 'ut.ny.na')
        self.failUnlessEqual(host.type, 'host')
        self.failUnlessEqual(host.personality.name, 'compileserver')
        self.failUnlessEqual(host.personality.archetype.name, 'aquilon')
        services = set()
        for svc_msg in host.services_used:
            services.add("%s/%s" % (svc_msg.service, svc_msg.instance))
        for binding in ("dns/unittest", "afs/q.ny.ms.com", "aqd/ny-prod"):
            self.failUnless(binding in services,
                            "Service binding %s is missing from protobuf "
                            "message. All bindings: %s" %
                            (binding, ",".join(list(services))))

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         '"hardware" = create("machine/americas/ut/ut3/ut3c1n3");',
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
                          r'"network_type", "unknown"\s*\),\s*' %
                          (self.net["unknown0"].broadcast,
                           self.net["unknown0"].gateway,
                           self.net["unknown0"].usable[2],
                           self.net["unknown0"].netmask),
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
                          r'"network_type", "unknown"\s*\)' %
                          (self.net["unknown0"].broadcast,
                           self.net["unknown0"].gateway,
                           self.net["unknown0"].usable[3],
                           self.net["unknown0"].netmask),
                          command)
        self.matchoutput(out, '"system/advertise_status" = false', command)

        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
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
                         """include { "service/bootserver/unittest/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "service/dns/unittest/client/config" };""",
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
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)
        self.matchclean(out, '"/metadata/template/branch/author"', command)

    def testverifyshowservicebyclient(self):
        command = "show service --client unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)
        self.matchoutput(out, "Service: bootserver Instance: unittest", command)
        self.matchoutput(out, "Service: dns Instance: unittest", command)
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
        # Note that make and reconfigure are basically the same thing for
        # a compileable archetype, so testing reconfigure --list here.
        # (This used to be a loop for make.)
        hosts = ["aquilon%d.aqd-unittest.ms.com\n" % i for i in range(61, 66)]
        scratchfile = self.writescratch("hpinventory", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile]
        (out, err) = self.successtest(command)
        for hostname in hosts:
            h = hostname.strip()
            self.matchoutput(err, "%s adding binding" % h, command)
        self.matchclean(err, "removing binding", command)

    def testmakerhel5(self):
        hosts = ["aquilon%d.aqd-unittest.ms.com\n" % i for i in range(66, 71)]
        scratchfile = self.writescratch("rhel5hosts", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--buildstatus=build", "--archetype=aquilon",
                   "--osname=linux", "--osversion=5.0.1-x86_64"]
        (out, err) = self.successtest(command)
        for hostname in hosts:
            h = hostname.strip()
            self.matchoutput(err, "%s adding binding" % h, command)
        self.matchclean(err, "removing binding", command)

    def testmakehpunixeng(self):
        hosts = ["aquilon%d.aqd-unittest.ms.com\n" % i for i in range(81, 90)]
        scratchfile = self.writescratch("hpunixeng", "".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype=aquilon", "--personality=unixeng-test"]
        (out, err) = self.successtest(command)
        for hostname in hosts:
            h = hostname.strip()
            self.matchoutput(err, "%s adding binding" % h, command)
        self.matchclean(err, "removing binding", command)
        self.matchoutput(err, "service instance chooser1", command)
        self.matchoutput(err, "service instance chooser2", command)
        self.matchoutput(err, "service instance chooser3", command)

    def testmissingrequiredservice(self):
        command = ["make", "aquilon",
                   "--hostname", "aquilon91.aqd-unittest.ms.com",
                   "--personality", "badpersonality2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not find a relevant service map", command)

    def testmissingrequiredservicedebug(self):
        command = ["make", "aquilon", "--debug",
                   "--hostname", "aquilon92.aqd-unittest.ms.com",
                   "--personality", "badpersonality2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Creating service chooser", command)
        self.matchoutput(out, "Could not find a relevant service map", command)

    def testmissingpersonalitytemplate(self):
        command = ["make", "aquilon",
                   "--hostname", "aquilon93.aqd-unittest.ms.com",
                   "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'/system/personality/function' does not have an associated value", command)
        self.failIf(os.path.exists(
            self.build_profile_name("aquilon93.aqd-unittest.ms.com",
                                    domain="unittest")))
        servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                  "servicedata")
        results = self.grepcommand(["-rl", "aquilon93.aqd-unittest.ms.com",
                                    servicedir])
        self.failIf(results, "Found service plenary data that includes "
                             "aquilon93.aqd-unittest.ms.com")

    def testmakecardedhost(self):
        command = ["make", "aquilon",
                   "--hostname", "jack.cards.example.com"]
        (out, err) = self.successtest(command)

    def testmakewithos(self):
        command = ["make", "aquilon",
                   "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64"]
        (out, err) = self.successtest(command)

    def testverifyunittest17(self):
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

    def testverifyunittest17proto(self):
        command = ["show_host", "--format=proto",
                   "--hostname=unittest17.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.assertEmptyErr(err, command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.assertEqual(host.fqdn, "unittest17.aqd-unittest.ms.com")
        #still fails, but it's checked below in the for loop
        self.assertEqual(host.ip, str(self.net["tor_net_0"].usable[3]))
        self.assertEqual(host.mac, self.net["tor_net_0"].usable[3].mac)
        self.assertEqual(host.machine.name, "ut8s02p3")
        self.assertEqual(len(host.machine.interfaces), 2)
        for i in host.machine.interfaces:
            if i.device == 'eth0':
                self.assertEqual(i.ip, str(self.net["tor_net_0"].usable[3]))
                self.assertEqual(i.mac, self.net["tor_net_0"].usable[3].mac)
            elif i.device == 'eth1':
                # Skipping IP test to avoid merge conflict
                self.assertEqual(i.mac, "")
            else:
                self.fail("Unrecognized interface '%s'" % i.device)

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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeAquilon)
    unittest.TextTestRunner(verbosity=2).run(suite)
