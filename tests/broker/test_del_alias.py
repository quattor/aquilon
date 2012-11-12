#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the del alias command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelAlias(TestBrokerCommand):
    def test_100_del_alias2host(self):
        command = ["del", "alias", "--fqdn", "alias2host.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Alias alias2host.aqd-unittest.ms.com still has "
                         "aliases, delete them first.", command)

    def test_110_del_missing(self):
        command = ["del", "alias", "--fqdn", "no-such-alias.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Alias no-such-alias.aqd-unittest.ms.com, DNS "
                         "environment internal not found.",
                         command)

    def test_200_del_alias4alias(self):
        command = ["del", "alias", "--fqdn", "alias4alias.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_201_del_alias3alias(self):
        command = ["del", "alias", "--fqdn", "alias3alias.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_202_del_alias2alias(self):
        command = ["del", "alias", "--fqdn", "alias2alias.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_210_del_alias2host(self):
        command = ["del", "alias", "--fqdn", "alias2host.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_220_del_mscom_alias(self):
        command = ["del", "alias", "--fqdn", "alias.ms.com"]
        self.dsdb_expect("delete_host_alias -alias_name alias.ms.com")
        self.noouttest(command)
        self.dsdb_verify()

    def test_300_del_restrict1(self):
        command = ["del", "alias", "--fqdn", "restrict1.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_301_verify_target(self):
        # There was a second alias, so the target must still exist
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target2.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Reserved Name: target2.restrict.aqd-unittest.ms.com",
                         command)

    def test_310_del_autotarget(self):
        command = ["del", "alias", "--fqdn", "restrict2.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_311_verify_target_gone(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target2.restrict.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_320_restricted_alias_no_dsdb(self):
        command = ["del", "alias", "--fqdn", "restrict.ms.com"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
