#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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
"""Module for testing the add/show alias command."""

if __name__ == '__main__':
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand


class TestAddAlias(TestBrokerCommand):
    def test_100_add_alias2host(self):
        cmd = ['add', 'alias', '--fqdn', 'alias2host.aqd-unittest.ms.com',
               '--target', 'arecord13.aqd-unittest.ms.com']
        self.noouttest(cmd)

    def test_105_add_aliasduplicate(self):
        cmd = ['add', 'alias', '--fqdn', 'alias2host.aqd-unittest.ms.com',
               '--target', 'arecord13.aqd-unittest.ms.com']
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Alias alias2host.aqd-unittest.ms.com "
                         "already exists.", cmd)

    def test_110_mscom_alias(self):
        cmd = ['add', 'alias', '--fqdn', 'alias.ms.com',
               '--target', 'arecord13.aqd-unittest.ms.com',
               '--comments', 'Some alias comments']
        self.dsdb_expect("add_host_alias "
                         "-host_name arecord13.aqd-unittest.ms.com "
                         "-alias_name alias.ms.com "
                         "-comments Some alias comments")
        self.noouttest(cmd)
        self.dsdb_verify()

    def test_120_conflict_a_record(self):
        cmd = ['add', 'alias', '--fqdn', 'arecord14.aqd-unittest.ms.com',
               '--target', 'arecord13.aqd-unittest.ms.com']
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "DNS Record arecord14.aqd-unittest.ms.com "
                         "already exists.", cmd)

    def test_130_conflict_reserver_name(self):
        cmd = ['add', 'alias', '--fqdn', 'nyaqd1.ms.com',
               '--target', 'arecord13.aqd-unittest.ms.com']
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Reserved Name nyaqd1.ms.com already exists.", cmd)

    def test_140_restricted_domain(self):
        cmd = ["add", "alias", "--fqdn", "foo.restrict.aqd-unittest.ms.com",
               "--target", "arecord13.aqd-unittest.ms.com"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, aliases are not allowed.",
                         cmd)

    def test_200_autocreate_target(self):
        cmd = ["add", "alias", "--fqdn", "restrict1.aqd-unittest.ms.com",
               "--target", "target.restrict.aqd-unittest.ms.com"]
        out = self.statustest(cmd)
        self.matchoutput(out,
                         "WARNING: Will create a reference to "
                         "target.restrict.aqd-unittest.ms.com, but ",
                         cmd)

    def test_201_verify_autocreate(self):
        cmd = ["search", "dns", "--fullinfo",
               "--fqdn", "target.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(cmd)
        self.matchoutput(out,
                         "Reserved Name: target.restrict.aqd-unittest.ms.com",
                         cmd)

    def test_201_verify_noprimary(self):
        cmd = ["search", "dns", "--noprimary_name",
               "--record_type", "reserved_name"]
        out = self.commandtest(cmd)
        self.matchoutput(out, "target.restrict.aqd-unittest.ms.com", cmd)

    def test_210_autocreate_second_alias(self):
        cmd = ["add", "alias", "--fqdn", "restrict2.aqd-unittest.ms.com",
               "--target", "target.restrict.aqd-unittest.ms.com"]
        self.noouttest(cmd)

    def test_220_restricted_alias_no_dsdb(self):
        cmd = ["add", "alias", "--fqdn", "restrict.ms.com",
               "--target", "no-dsdb.restrict.aqd-unittest.ms.com"]
        out = self.statustest(cmd)
        self.matchoutput(out,
                         "WARNING: Will create a reference to "
                         "no-dsdb.restrict.aqd-unittest.ms.com, but ",
                         cmd)
        self.dsdb_verify(empty=True)

    def test_400_verify_alias2host(self):
        cmd = "show alias --fqdn alias2host.aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))

        self.matchoutput(out, "Alias: alias2host.aqd-unittest.ms.com", cmd)
        self.matchoutput(out, "Target: arecord13.aqd-unittest.ms.com", cmd)
        self.matchoutput(out, "DNS Environment: internal", cmd)

    def test_405_verify_host_shows_alias(self):
        cmd = "show address --fqdn arecord13.aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Aliases: alias.ms.com, "
                         "alias2host.aqd-unittest.ms.com", cmd)

    def test_410_verify_mscom_alias(self):
        cmd = "show alias --fqdn alias.ms.com"
        out = self.commandtest(cmd.split(" "))

        self.matchoutput(out, "Alias: alias.ms.com", cmd)
        self.matchoutput(out, "Target: arecord13.aqd-unittest.ms.com", cmd)
        self.matchoutput(out, "DNS Environment: internal", cmd)
        self.matchoutput(out, "Comments: Some alias comments", cmd)

    def test_500_add_alias2alias(self):
        cmd = ['add', 'alias', '--fqdn', 'alias2alias.aqd-unittest.ms.com',
               '--target', 'alias2host.aqd-unittest.ms.com']
        self.noouttest(cmd)

    def test_510_add_alias3alias(self):
        cmd = ['add', 'alias', '--fqdn', 'alias3alias.aqd-unittest.ms.com',
               '--target', 'alias2alias.aqd-unittest.ms.com']
        self.noouttest(cmd)

    def test_520_add_alias4alias(self):
        cmd = ['add', 'alias', '--fqdn', 'alias4alias.aqd-unittest.ms.com',
               '--target', 'alias3alias.aqd-unittest.ms.com']
        self.noouttest(cmd)

    def test_530_add_alias5alias_fail(self):
        cmd = ['add', 'alias', '--fqdn', 'alias5alias.aqd-unittest.ms.com',
               '--target', 'alias4alias.aqd-unittest.ms.com']
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Maximum alias depth exceeded", cmd)

    def test_600_verify_alias2alias(self):
        cmd = 'show alias --fqdn alias2alias.aqd-unittest.ms.com'
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, 'Alias: alias2alias.aqd-unittest.ms.com', cmd)

    def test_601_verify_alias2alias_backwards(self):
        cmd = 'show alias --fqdn alias2host.aqd-unittest.ms.com'
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Aliases: alias2alias.aqd-unittest.ms.com", cmd)

    def test_602_verify_alias2alias_recursive(self):
        cmd = 'show address --fqdn arecord13.aqd-unittest.ms.com'
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out,
                         "Aliases: alias.ms.com, "
                         "alias2alias.aqd-unittest.ms.com, "
                         "alias2host.aqd-unittest.ms.com, "
                         "alias3alias.aqd-unittest.ms.com, "
                         "alias4alias.aqd-unittest.ms.com",
                         cmd)

    def test_700_show_alias_host(self):
        command = ["add", "alias", "--fqdn", "alias0.aqd-unittest.ms.com",
                   "--target", "unittest20-e0.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["add", "alias", "--fqdn", "alias01.aqd-unittest.ms.com",
                   "--target", "alias0.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'Provides: unittest20-e0.aqd-unittest.ms.com \[4.2.12.5\]\s*'
                               r'Aliases: alias0.aqd-unittest.ms.com, alias01.aqd-unittest.ms.com',
                          command)

        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--format", "proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.failUnlessEqual(host.hostname, 'unittest20')
        int = host.machine.interfaces[0]
        self.failUnlessEqual(int.aliases[0], 'alias0.aqd-unittest.ms.com')
        self.failUnlessEqual(int.aliases[1], 'alias01.aqd-unittest.ms.com')
        self.failUnlessEqual(int.ip, '4.2.12.5')
        self.failUnlessEqual(int.fqdn, 'unittest20-e0.aqd-unittest.ms.com')

        command = ["del", "alias", "--fqdn", "alias01.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["del", "alias", "--fqdn", "alias0.aqd-unittest.ms.com"]
        out = self.commandtest(command)

    def test_710_show_alias_host(self):
        command = ["add", "alias", "--fqdn", "alias1.aqd-unittest.ms.com",
                   "--target", "unittest20-e1-1.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["add", "alias", "--fqdn", "alias11.aqd-unittest.ms.com",
                   "--target", "alias1.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'Provides: unittest20-e1-1.aqd-unittest.ms.com \[4.2.12.72\] \(label: e1\)\s*'
                               r'Aliases: alias1.aqd-unittest.ms.com, alias11.aqd-unittest.ms.com',
                          command)

        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--format", "proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.failUnlessEqual(host.hostname, 'unittest20')
        int = host.machine.interfaces[5]
        self.failUnlessEqual(int.aliases[0], 'alias1.aqd-unittest.ms.com')
        self.failUnlessEqual(int.aliases[1], 'alias11.aqd-unittest.ms.com')
        self.failUnlessEqual(int.ip, '4.2.12.72')
        self.failUnlessEqual(int.fqdn, 'unittest20-e1-1.aqd-unittest.ms.com')

        command = ["del", "alias", "--fqdn", "alias11.aqd-unittest.ms.com"]
        out = self.commandtest(command)

        command = ["del", "alias", "--fqdn", "alias1.aqd-unittest.ms.com"]
        out = self.commandtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
