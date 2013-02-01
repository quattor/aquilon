#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Module for testing the dump_dns command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


def inaddr_ptr(ip):
    octets = str(ip).split('.')
    octets.reverse()
    return "%s.in-addr.arpa" % '.'.join(octets)


class TestDumpDns(TestBrokerCommand):

    def test_djb(self):
        command = ["dump", "dns"]
        out = self.commandtest(command, auth=False)
        # Primary name
        self.matchoutput(out,
                         "=unittest20.aqd-unittest.ms.com:%s" %
                         self.net.unknown[13].usable[2],
                         command)
        # Auxiliary address
        self.matchoutput(out,
                         "+unittest20-e0.aqd-unittest.ms.com:%s" %
                         self.net.unknown[11].usable[0],
                         command)
        self.matchoutput(out,
                         "^%s:unittest20.aqd-unittest.ms.com" %
                         inaddr_ptr(self.net.unknown[11].usable[0]),
                         command)
        # CNAME
        self.matchoutput(out,
                         "Calias2host.aqd-unittest.ms.com:arecord13.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out,
                         "Calias2alias.aqd-unittest.ms.com:alias2host.aqd-unittest.ms.com",
                         command)
        # SRV
        self.matchoutput(out,
                         r":_kerberos._tcp.aqd-unittest.ms.com:33:\000\012\000\024\000\130\011arecord14\014aqd-unittest\002ms\003com\000",
                         command)
        self.matchoutput(out,
                         r":_kerberos._tcp.aqd-unittest.ms.com:33:\000\012\000\024\000\130\011arecord15\014aqd-unittest\002ms\003com\000",
                         command)
        self.matchclean(out, "utcolo", command)

    def test_djb_domain(self):
        command = ["dump", "dns", "--dns_domain", "one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "aqd-unittest.ms.com", command)

    def test_djb_env(self):
        command = ["dump", "dns", "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        # The primary name is in a different DNS environment, so we can't
        # reference it in the reverse record
        self.matchoutput(out,
                         "=unittest25-e1.utcolo.aqd-unittest.ms.com:%s" %
                         self.net.unknown[1][4],
                         command)

    def test_bind(self):
        command = ["dump", "dns", "--format", "raw"]
        out = self.commandtest(command)
        # Primary name
        self.matchoutput(out,
                         "unittest20.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net.unknown[13].usable[2],
                         command)
        self.matchoutput(out,
                         "%s.\tIN\tPTR\tunittest20.aqd-unittest.ms.com." %
                         inaddr_ptr(self.net.unknown[13].usable[2]),
                         command)
        # Auxiliary address
        self.matchoutput(out,
                         "unittest20-e0.aqd-unittest.ms.com.\tIN\tA\t%s" %
                         self.net.unknown[11].usable[0],
                         command)
        self.matchoutput(out,
                         "%s.\tIN\tPTR\tunittest20.aqd-unittest.ms.com." %
                         inaddr_ptr(self.net.unknown[11].usable[0]),
                         command)
        # CNAME
        self.matchoutput(out,
                         'alias2host.aqd-unittest.ms.com.\tIN\tCNAME\tarecord13.aqd-unittest.ms.com.',
                         command)
        self.matchoutput(out,
                         'alias2alias.aqd-unittest.ms.com.\tIN\tCNAME\talias2host.aqd-unittest.ms.com.',
                         command)
        # SRV
        self.matchoutput(out,
                         "_kerberos._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 88 arecord14.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(out,
                         "_kerberos._tcp.aqd-unittest.ms.com.\tIN\tSRV\t"
                         "10 20 88 arecord15.aqd-unittest.ms.com.",
                         command)
        self.matchclean(out, "utcolo", command)

    def test_bind_domain(self):
        command = ["dump", "dns", "--dns_domain", "one-nyp.ms.com",
                   "--format", "raw"]
        out = self.commandtest(command)
        self.matchclean(out, "aqd-unittest.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDumpDns)
    unittest.TextTestRunner(verbosity=2).run(suite)
