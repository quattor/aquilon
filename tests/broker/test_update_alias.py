#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the update archetype command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateAlias(TestBrokerCommand):

    def test_100_update(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_110_update_mscom(self):
        command = ["update", "alias", "--fqdn", "alias.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--comments", "Other alias comments"]
        self.dsdb_expect("update_host_alias "
                         "-alias alias.ms.com "
                         "-new_host arecord14.aqd-unittest.ms.com "
                         "-new_comments Other alias comments")
        self.noouttest(command)
        self.dsdb_verify()

    def test_200_missing_target(self):
        command = ["update", "alias",
                   "--fqdn", "alias2host.aqd-unittest.ms.com",
                   "--target", "no-such-name.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Target FQDN no-such-name.aqd-unittest.ms.com "
                         "does not exist in DNS environment internal.",
                         command)

    def test_210_not_an_alias(self):
        command = ["update", "alias",
                   "--fqdn", "arecord13.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Alias arecord13.aqd-unittest.ms.com not found.",
                         command)

    def test_300_verify_alias(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "alias2host.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)

    def test_310_verify_mscom(self):
        command = ["search", "dns", "--fullinfo", "--fqdn", "alias.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Comments: Other alias comments", command)

    def test_320_verify_oldtarget(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord13.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "alias2host.aqd-unittest.ms.com", command)
        self.matchclean(out, "alias.ms.com", command)

    def test_330_verify_newtarget(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Aliases: alias.ms.com, "
                         "alias2alias.aqd-unittest.ms.com, "
                         "alias2host.aqd-unittest.ms.com", command)

    def test_400_repoint_restrict1(self):
        command = ["update", "alias", "--fqdn", "restrict1.aqd-unittest.ms.com",
                   "--target", "target2.restrict.aqd-unittest.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "WARNING: Will create alias for target "
                         "target2.restrict.aqd-unittest.ms.com, but ",
                         command)

    def test_410_verify_target(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'Aliases: restrict2.aqd-unittest.ms.com$',
                          command)

    def test_410_verify_target2(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target2.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'Aliases: restrict1.aqd-unittest.ms.com$',
                          command)

    def test_420_repoint_restrict2(self):
        command = ["update", "alias", "--fqdn", "restrict2.aqd-unittest.ms.com",
                   "--target", "target2.restrict.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_430_verify_target_gone(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target.restrict.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_430_verify_target2(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "target2.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Aliases: restrict1.aqd-unittest.ms.com, "
                         "restrict2.aqd-unittest.ms.com",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
