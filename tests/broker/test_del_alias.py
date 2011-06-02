#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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

    def test_200_del_alias2alias(self):
        command = ["del", "alias", "--fqdn", "alias2alias.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_210_del_alias2host(self):
        command = ["del", "alias", "--fqdn", "alias2host.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_220_del_mscom_alias(self):
        command = ["del", "alias", "--fqdn", "alias.ms.com"]
        self.dsdb_expect("delete host alias -alias_name alias.ms.com")
        self.noouttest(command)
        self.dsdb_verify()


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
