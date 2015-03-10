#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the reconfigure command."""


import os
import re
from datetime import datetime

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin
from broker.notificationtest import VerifyNotificationsMixin


class TestReconfigure(VerifyGrnsMixin, VerifyNotificationsMixin,
                      TestBrokerCommand):
    linux_version_prev = None
    linux_version_curr = None

    # Note that some tests for reconfigure --list appear in
    # test_make_aquilon.py.

    @classmethod
    def setUpClass(cls):
        super(TestReconfigure, cls).setUpClass()
        cls.linux_version_prev = cls.config.get("unittest",
                                                "linux_version_prev")
        cls.linux_version_curr = cls.config.get("unittest",
                                                "linux_version_curr")

    # If we end up fixing map dns domain, it may be harder to do this test.
    # Also, these tests would just "keep working", but they wouldn't
    # actually be testing anything...
    def test_1000_reconfigure_aquilon95(self):
        command = ["reconfigure", "--hostname=aquilon95.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_1001_verify_machine_plenary(self):
        command = ["cat", "--machine=ut9s03p45"]
        out = self.commandtest(command)
        self.matchoutput(out, '"rack/room" = "utroom2";', command)
        self.matchoutput(out, '"sysloc/bunker" = "bucket2.ut";', command)
        self.matchoutput(out, '"sysloc/building" = "ut";', command)
        self.matchoutput(out, '"sysloc/city" = "ny";', command)
        self.matchoutput(out, '"sysloc/continent" = "na";', command)
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = '
                          r'list\(\s*"new-york.ms.com"\s*\);',
                          command)

    def test_1002_map_dns_domain(self):
        out = self.successtest(['map_dns_domain', '--building=ut',
                                '--dns_domain=aqd-unittest.ms.com'])

    def test_1003_reconfigure_aquilon95(self):
        command = ["reconfigure", "--hostname=aquilon95.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)

    def test_1004_verify_machine_plenary(self):
        command = ["cat", "--machine=ut9s03p45"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = '
                          r'list\(\s*"aqd-unittest.ms.com",\s*'
                          r'"new-york.ms.com"\s*\);',
                          command)

    def test_1005_unmap_dns_domain(self):
        out = self.successtest(['unmap_dns_domain', '--building=ut',
                                '--dns_domain=aqd-unittest.ms.com'])

    def test_1006_reconfigure_aquilon95(self):
        command = ["reconfigure", "--hostname=aquilon95.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)

    def test_1007_verify_machine_plenary(self):
        command = ["cat", "--machine=ut9s03p45"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = '
                          r'list\(\s*"new-york.ms.com"\s*\);',
                          command)

    def test_1010_reconfigurelist_grn_pre(self):
        hosts = ["aquilon95.aqd-unittest.ms.com",
                 "aquilon91.aqd-unittest.ms.com"]
        for h in hosts:
            command = "show host --hostname %s" % h
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest", command)

    def test_1011_list_grn(self):
        hosts = ["aquilon95.aqd-unittest.ms.com",
                 "aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("grnlist", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--grn=grn:/ms/ei/aquilon/aqd"]
        self.successtest(command)

    def test_1015_reconfigurelist_grn_post(self):
        hosts = ["aquilon95.aqd-unittest.ms.com",
                 "aquilon91.aqd-unittest.ms.com"]
        for h in hosts:
            command = "show host --hostname %s" % h
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_1020_reconfigurelist_cleargrn_pre(self):
        hosts = ["aquilon95.aqd-unittest.ms.com"]
        for h in hosts:
            command = "show host --hostname %s" % h
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_1021_reconfigurelist_cleargrn(self):
        hosts = ["aquilon95.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("grnlist", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile, "--cleargrn"]
        out = self.successtest(command)

    def test_1025_reconfigurelist_cleargrn_post(self):
        hosts = ["aquilon95.aqd-unittest.ms.com"]
        for h in hosts:
            command = "show host --hostname %s" % h
            out = self.commandtest(command.split(" "))
            self.searchclean(out, "^  Owned by GRN", command)

    def test_1030_reconfigure_cleargrn(self):
        command = "show host --hostname aquilon91.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

        command = ["reconfigure", "--hostname", "aquilon91.aqd-unittest.ms.com",
                   "--cleargrn"]
        out = self.successtest(command)

        command = "show host --hostname aquilon91.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.searchclean(out, "^  Owned by GRN", command)

    def test_1040_reconfigure_membersof_cluster(self):
        # This will exercise the cluster-aligned services code,
        # which does not kick in at 'make' time because the hosts
        # have not been bound to clusters yet.
        command = ["reconfigure", "--membersof", "utecl1"]
        out = self.statustest(command)
        self.matchoutput(out, "/3 object template(s) being processed",
                         command)

    def test_1040_reconfigure_membersof_metacluster(self):
        command = ["reconfigure", "--membersof", "utmc1"]
        out = self.statustest(command)
        self.matchoutput(out, "/5 object template(s) being processed",
                         command)

    def test_1050_cat_unittest02_pre(self):
        command = "cat --hostname unittest02.one-nyp.ms.com --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"system/build" = "build";', command)
        self.matchoutput(out, '"system/owner_eon_id" = %d;' %
                         self.grns["grn:/ms/ei/aquilon/unittest"], command)

    # The rebind test has changed the service bindings for afs,
    # it should now be set to q.ln.ms.com.  The reconfigure will
    # force it *back* to using a correct service map entry, in
    # this case q.ny.ms.com.
    def test_1051_reconfigure_unittest02(self):
        basetime = datetime.now()
        command = ["reconfigure", "--hostname", "unittest02.one-nyp.ms.com",
                   "--buildstatus", "ready", "--grn", "grn:/ms/ei/aquilon/aqd"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance afs/q.ny.ms.com",
                         command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com removing binding for "
                         "service instance afs/q.ln.ms.com",
                         command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

    def test_1055_show_unittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: ready", command)
        self.matchoutput(out, "Advertise Status: True", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_1055_cat_unittest02_data(self):
        command = "cat --hostname unittest02.one-nyp.ms.com --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template hostdata/unittest02.one-nyp.ms.com;",
                         command)
        self.matchoutput(out,
                         '"hardware" = create("machine/americas/ut/ut3/ut3c5n10");',
                         command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest02.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (self.net["unknown0"].broadcast,
                           self.net["unknown0"].gateway,
                           self.net["unknown0"].usable[0],
                           self.net["unknown0"].netmask,
                           self.net["unknown0"].gateway),
                          command)
        self.matchoutput(out, '"system/advertise_status" = true;', command)
        self.matchoutput(out, '"system/owner_eon_id" = %d;' %
                         self.grns["grn:/ms/ei/aquilon/aqd"], command)

        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "object template unittest02.one-nyp.ms.com;",
                         command)
        self.searchoutput(out,
                          r'variable LOADPATH = list\(\s*"aquilon"\s*\);',
                          command)

        self.matchoutput(out,
                         """include { "archetype/base" };""",
                         command)
        self.matchoutput(out,
                         """\"/\" = create(\"hostdata/unittest02.one-nyp.ms.com\"""",
                         command)
        self.matchoutput(out,
                         'include { "os/linux/%s/config" };' %
                         self.linux_version_prev,
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

    # These settings have not changed - the command should still succeed.
    def test_1060_reconfigur_eunittest00(self):
        basetime = datetime.now()
        command = ["reconfigure", "--hostname", "unittest00.one-nyp.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)
        self.matchoutput(err, "Index rebuild and notifications will happen in "
                         "the background.", command)
        self.wait_notification(basetime, 1)

    def test_1065_cat_unittest00_data(self):
        command = "cat --hostname unittest00.one-nyp.ms.com --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template hostdata/unittest00.one-nyp.ms.com;",
                         command)
        self.matchoutput(out,
                         '"hardware" = create("machine/americas/ut/ut3/ut3c1n3");',
                         command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest00.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (self.net["unknown0"].broadcast,
                           self.net["unknown0"].gateway,
                           self.net["unknown0"].usable[2],
                           self.net["unknown0"].netmask,
                           self.net["unknown0"].gateway),
                          command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth1" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest00-e1.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "%s",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (self.net["unknown0"].broadcast,
                           self.net["unknown0"].gateway,
                           self.net["unknown0"].usable[3],
                           self.net["unknown0"].netmask,
                           self.net["unknown0"].gateway),
                          command)
        self.matchoutput(out, '"system/advertise_status" = false;', command)

    def test_1065_cat_unittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         """include { "archetype/base" };""",
                         command)
        self.matchoutput(out,
                         """\"/\" = create(\"hostdata/unittest00.one-nyp.ms.com\"""",
                         command)
        self.matchoutput(out,
                         'include { "os/linux/%s/config" };' %
                         self.linux_version_prev,
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

    def test_1070_reconfigure_windows_status(self):
        # Not a compileable archetype, so there should be no messages from the
        # compiler
        self.noouttest(["reconfigure",
                        "--hostname", "unittest01.one-nyp.ms.com",
                        "--buildstatus", "ready"])

    def test_1071_reconfigure_windows_personality(self):
        # Not a compileable archetype, so there should be no messages from the
        # compiler
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--personality", "desktop"]
        self.noouttest(command)

    def test_1072_reconfigure_windows_os(self):
        # Not a compileable archetype, so there should be no messages from the
        # compiler
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--osversion", "nt61e"]
        self.noouttest(command)

    def test_1075_show_unittest01(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: desktop", command)
        self.matchoutput(out, "Build Status: ready", command)
        self.matchoutput(out, "Operating System: windows", command)
        self.matchoutput(out, "Version: nt61e", command)
        self.matchoutput(out, "Advertise Status: True", command)

    def test_1080_reconfigure_os(self):
        command = ["reconfigure",
                   "--hostname", "aquilon61.aqd-unittest.ms.com",
                   "--osname", "linux", "--osversion", self.linux_version_curr]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def test_1085_reconfigure_os_split_args(self):
        command = ["reconfigure",
                   "--hostname", "unittest17.aqd-unittest.ms.com",
                   "--osname", "linux", "--osversion", self.linux_version_curr]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def test_1090_keepbindings(self):
        command = ["reconfigure", "--keepbindings",
                   "--hostname", "aquilon86.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template", command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def test_1100_remove_bindings(self):
        command = ["reconfigure",
                   "--hostname", "aquilon87.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "removing binding for service instance chooser1", command)
        self.matchoutput(err, "removing binding for service instance chooser2", command)
        self.matchoutput(err, "removing binding for service instance chooser3", command)
        self.matchclean(err, "adding binding", command)

    def test_1105_verify_services(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["search_host", "--service", service,
                       "--hostname", "aquilon87.aqd-unittest.ms.com"]
            self.noouttest(command)

    def test_1105_verify_plenary_data(self):
        command = "cat --hostname aquilon87.aqd-unittest.ms.com --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template hostdata/aquilon87.aqd-unittest.ms.com;",
                         command)
        self.matchoutput(out,
                         '"hardware" = create("machine/americas/ut/ut9/ut9s03p37");',
                         command)

    def test_1105_verify_plenary(self):
        osversion = self.config.get("archetype_aquilon", "default_osversion")
        command = "cat --hostname aquilon87.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "chooser1", command)
        self.matchclean(out, "chooser2", command)
        self.matchclean(out, "chooser3", command)
        self.matchoutput(out,
                         """include { "archetype/base" };""",
                         command)
        self.matchoutput(out,
                         """\"/\" = create(\"hostdata/aquilon87.aqd-unittest.ms.com\"""",
                         command)
        self.matchoutput(out,
                         'include { "os/linux/%s/config" };' % osversion,
                         command)
        self.matchoutput(out,
                         """include { "service/aqd/ny-prod/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "service/ntp/pa.ny.na/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "service/bootserver/unittest/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "service/afs/q.ny.ms.com/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "service/dns/unittest/client/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "personality/inventory/config" };""",
                         command)
        self.matchoutput(out,
                         """include { "archetype/final" };""",
                         command)

    def test_1110_reconfigure_debug(self):
        command = ["reconfigure", "--debug",
                   "--hostname", "aquilon88.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Creating service chooser", command)

    def test_1120_reconfigure_aligned(self):
        for i in range(1, 5):
            command = ["reconfigure",
                       "--hostname", "evh%s.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)

    def test_1125_verify_aligned(self):
        # Check that utecl1 is now aligned to a service and that
        # all of its members are aligned to the same service.
        # evh[234] should be bound to utecl1
        command = "show esx cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        m = re.search(r'Member Alignment: Service esx_management_server '
                      r'Instance (\S+)', out)
        self.assertTrue(m, "Aligned instance not found in output:\n%s" % out)
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

    def test_1130_list_camelcase(self):
        hosts = ["Aquilon91.Aqd-Unittest.ms.com"]
        scratchfile = self.writescratch("camelcase", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile]
        self.successtest(command)

    def test_1140_list_no_osversion(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingosversion", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile, "--osname=linux"]
        self.successtest(command)

    def test_1150_list_no_osname(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingosname", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--osversion=%s" % self.linux_version_prev]
        self.successtest(command)

    def test_1160_list_no_os_archetype(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingosarchetype", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--osname=linux", "--osversion=%s" % self.linux_version_prev]
        self.successtest(command)

    def test_2000_windows_wrong_os(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--osname", "linux", "--osversion", self.linux_version_prev]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Operating System linux, version %s, archetype "
                         "windows not found." % self.linux_version_prev,
                         command)

    def test_2000_os_archetype_mismatch(self):
        # Trying to change archetype, but there's no suitable OS
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--archetype", "aquilon", "--personality", "unixeng-test"]
        err = self.notfoundtest(command)
        self.matchoutput(err,
                         "Operating System windows, version nt61e, "
                         "archetype aquilon not found.",
                         command)

    def test_2000_os_archetype_mismatch_list(self):
        hosts = ["unittest01.one-nyp.ms.com"]
        scratchfile = self.writescratch("hostlist", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype", "aquilon", "--personality=unixeng-test"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "unittest01.one-nyp.ms.com: Operating System "
                         "windows, version nt61e, archetype aquilon not found.",
                         command)

    def test_2000_missing_personality(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--archetype", "windows"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality inventory, archetype windows not found.",
                         command)

    def test_2000_personality_not_allowed(self):
        command = ["reconfigure", "--hostname=evh2.aqd-unittest.ms.com",
                   "--personality=esx_server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Personality vmhost/esx_server is not allowed by "
                         "ESX Cluster utecl1.  Specify one of: "
                         "vmhost/vulcan-1g-desktop-prod.",
                         command)

    def test_2000_personality_not_allowed_list(self):
        hosts = ["evh2.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("persnotallowed", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype=vmhost", "--personality=esx_server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "evh2.aqd-unittest.ms.com: Personality "
                         "vmhost/esx_server is not allowed by ESX Cluster "
                         "utecl1.  Specify one of: vmhost/vulcan-1g-desktop-prod.",
                         command)

    def test_2000_hostlist_multiple_domains(self):
        hosts = ["unittest02.one-nyp.ms.com",
                 "server1.aqd-unittest.ms.com",
                 "server2.aqd-unittest.ms.com",
                 "evh1.aqd-unittest.ms.com",
                 "aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("diffdomains", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "All hosts must be in the same domain or sandbox:", command)
        self.matchoutput(out, "3 hosts in sandbox %s/utsandbox" % self.user, command)
        self.matchoutput(out, "2 hosts in domain unittest", command)

    def test_2000_missing_required_service(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingmap", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype", "aquilon",
                   "--personality", "badpersonality2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not find a relevant service map", command)
        self.matchoutput(out, "The following hosts failed service binding:",
                         command)
        self.matchoutput(out, "aquilon91.aqd-unittest.ms.com", command)

    def test_2000_list_personality_no_archetype(self):
        hosts = ["aquilon91.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingarchetype", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--personality=generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Personality generic, archetype aquilon not found.",
                         command)

    def test_2000_empty_hostlist(self):
        hosts = ["#host", "#does", "", "   #not   ", "#exist"]
        scratchfile = self.writescratch("empty", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Empty list.", command)

    def test_2000_bad_hosts_in_list(self):
        hosts = ["host-does-not-exist.aqd-unittest.ms.com",
                 "another-host-does-not-exist.aqd-unittest.ms.com",
                 "aquilon91.aqd-unittest.ms.com",
                 "host.domain-does-not-exist.ms.com"]
        scratchfile = self.writescratch("missinghost", "\n".join(hosts))
        # Use the deprecated option name here
        command = ["reconfigure", "--hostlist", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The --hostlist option is deprecated.", command)
        self.matchoutput(out, "Invalid hosts in list:", command)
        self.matchoutput(out,
                         "Host host-does-not-exist.aqd-unittest.ms.com not found.",
                         command)
        self.matchoutput(out,
                         "Host another-host-does-not-exist.aqd-unittest.ms.com not found.",
                         command)
        self.matchoutput(out,
                         "Host host.domain-does-not-exist.ms.com not found.",
                         command)
        self.matchoutput(out,
                         "DNS Domain domain-does-not-exist.ms.com not found.",
                         command)
        self.matchclean(out, "aquilon91.aqd-unittest.ms.com:", command)

    def test_2000_over_list_limit(self):
        hostlimit = self.config.getint("broker", "reconfigure_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com" % i)
        scratchfile = self.writescratch("reconfigurelistlimit", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile, "--personality=generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)

    def test_3000_missing_required_params(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'/system/personality/function' does not have an associated value", command)
        buildfile = self.build_profile_name("aquilon62.aqd-unittest.ms.com",
                                            domain="utsandbox")
        results = self.grepcommand(["-l", "badpersonality", buildfile])
        self.assertFalse(results, "Found bad personality data in plenary "
                         "template for aquilon62.aqd-unittest.ms.com")

    def test_3010_missing_personality_template_hostlist(self):
        hosts = ["aquilon93.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("missingtemplate", "\n".join(hosts))
        command = ["reconfigure", "--list", scratchfile,
                   "--archetype", "aquilon", "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'/system/personality/function' does not have an associated value", command)
        self.assertFalse(os.path.exists(
            self.build_profile_name("aquilon93.aqd-unittest.ms.com",
                                    domain="utsandbox")))
        servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                  "servicedata")
        results = self.grepcommand(["-rl", "aquilon93.aqd-unittest.ms.com",
                                    servicedir])
        self.assertFalse(results, "Found service plenary data that includes "
                         "aquilon93.aqd-unittest.ms.com")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReconfigure)
    unittest.TextTestRunner(verbosity=2).run(suite)
