#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Module for testing the add/show alias command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


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
               '--target', 'arecord13.aqd-unittest.ms.com']
        self.dsdb_expect("add host alias "
                         "-host_name arecord13.aqd-unittest.ms.com "
                         "-alias_name alias.ms.com "
                         "-comments ")
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
                         "WARNING: Will create alias for target "
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
                         "WARNING: Will create alias for target "
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

    def test_500_add_alias2alias(self):
        cmd = ['add', 'alias', '--fqdn', 'alias2alias.aqd-unittest.ms.com',
               '--target', 'alias2host.aqd-unittest.ms.com']
        self.noouttest(cmd)

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
                         "alias2host.aqd-unittest.ms.com",
                         cmd)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
