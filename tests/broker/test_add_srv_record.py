#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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
"""Module for testing the add/show srv record command."""

import unittest

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddSrvRecord(TestBrokerCommand):

    def test_100_add_kerberos1(self):
        command = ["add", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 88, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_110_add_kerberos2(self):
        command = ["add", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--port", 88, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_120_add_kerberos2_dup(self):
        command = ["add", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--port", 88, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "SRV Record _kerberos._tcp.aqd-unittest.ms.com "
                         "already exists.", command)

    def test_130_add_ldap(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        self.noouttest(command)

    def test_200_show_srvrec(self):
        command = ["show", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _kerberos._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: kerberos", command)
        self.matchoutput(out, "Protocol: tcp", command)
        self.matchoutput(out, "Priority: 10", command)
        self.matchoutput(out, "Weight: 20", command)
        # TODO: emphasize that there are two records
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Target: arecord15.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Port: 88", command)
        self.matchclean(out, "Port: 389", command)

    def test_210_search_srvrec(self):
        command = ["search", "dns", "--record_type", "srv"]
        out = self.commandtest(command)
        self.matchoutput(out, "_kerberos._tcp.aqd-unittest.ms.com", command)
        self.matchoutput(out, "_ldap._tcp.aqd-unittest.ms.com", command)
        self.matchclean(out, "alias", command)
        self.matchclean(out, "arecord", command)
        self.matchclean(out, "unittest0", command)

    def test_220_search_bytarget(self):
        command = ["search", "dns", "--target", "arecord14.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "SRV Record: _kerberos._tcp.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Service: kerberos", command)
        self.matchoutput(out, "Protocol: tcp", command)
        self.matchoutput(out, "Priority: 10", command)
        self.matchoutput(out, "Weight: 20", command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Port: 88", command)
        self.matchclean(out, "arecord15.aqd-unittest.ms.com", command)

    def test_300_badport(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 0, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The port must be between 1 and 65535.", command)

    def test_310_badprio(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 65536, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The priority must be between 0 and 65535.", command)

    def test_320_badproto(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "badproto", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown protocol badproto.", command)

    def test_330_alias(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "badproto", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "alias2host.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The target of an SRV record must not be an alias.",
                         command)

    def test_340_reservedname(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "badproto", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "nyaqd1.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The target of an SRV record must resolve to one or "
                         "more addresses.",
                         command)

    def test_350_restricted(self):
        command = ["add", "srv", "record", "--service", "ldap",
                   "--protocol", "badproto",
                   "--dns_domain", "restrict.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--port", 389, "--priority", 10, "--weight", 20]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, SRV records are not allowed.",
                         command)

    def test_360_show_missing(self):
        command = ["show", "srv", "record", "--service", "no-such-service",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SRV Record for service no-such-service, protocol "
                         "tcp in DNS domain aqd-unittest.ms.com not found.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddSrvRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
