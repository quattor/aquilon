#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Module for testing the add/show dns_record command(s)."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

DOMAIN = 'aqd-unittest.ms.com'
NAME = 'dnstest1.%s' % DOMAIN
NET_OFFSET = 10
DJB = '--format djb'
CSV = '--format csv'


class TestAddNSRecord(TestBrokerCommand):
    """ The tests for adding and displaying NS Records"""

    def setUp(self, *args, **kwargs):
        super(TestAddNSRecord, self).setUp(*args, **kwargs)
        self.NETWORK = self.net.unknown[NET_OFFSET]
        self.IP = str(self.net.unknown[NET_OFFSET].usable[0])

    def test_100_add_a_record(self):
        self.dsdb_expect_add(NAME, self.IP)
        cmd = ['add', 'address', '--fqdn', NAME, '--ip', self.IP]
        self.noouttest(cmd)
        self.dsdb_verify()

    def test_200_verify_a_record(self):
        cmd = "show address --fqdn %s" % NAME
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "DNS Record: %s" % NAME, cmd)

    def test_300_add_ns_record(self):
        cmd = "add ns_record --dns_domain %s --fqdn %s" % (DOMAIN, NAME)
        self.noouttest(cmd.split(" "))

    def test_305_add_ns_record_duplicate(self):
        cmd = "add ns_record --dns_domain %s --fqdn %s" % (DOMAIN, NAME)
        self.badrequesttest(cmd.split(" "))

    def test_400_verify_ns_record(self):
        cmd = "show ns record --dns_domain %s --fqdn %s" % (DOMAIN, NAME)
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, NAME, cmd)

    def test_401_verify_ns_record_in_dns_domain(self):
        cmd = 'show dns_domain --dns_domain %s' % DOMAIN
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, 'DNS Domain: %s' % DOMAIN, cmd)
        self.matchoutput(out, NAME, cmd)

    def test_402_verify_ns_record_djb(self):
        cmd = "show ns record --dns_domain %s --fqdn %s %s" % (
             DOMAIN, NAME, DJB)
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, '.%s::%s' % (DOMAIN, NAME), cmd)

    def test_410_verify_ns_record_csv(self):
        cmd = "show ns record --dns_domain %s --fqdn %s %s" % (
             DOMAIN, NAME, CSV)
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, '%s,%s' % (DOMAIN, NAME), cmd)


if __name__ == '__main__':
    import nose
    nose.runmodule()
