#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016,2017  Contributor
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
"""Module for testing the add/show dns_record command(s)."""

import unittest

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

DOMAIN = 'aqd-unittest.ms.com'
NAME = 'dnstest1.%s' % DOMAIN
DJB = '--format djb'
CSV = '--format csv'
GRN = 'grn:/ms/ei/aquilon/aqd'

class TestAddNSRecord(TestBrokerCommand):
    """ The tests for adding and displaying NS Records"""

    def setUp(self, *args, **kwargs):
        super(TestAddNSRecord, self).setUp(*args, **kwargs)
        self.NETWORK = self.net["ut9_chassis"]
        self.IP = str(self.net["ut9_chassis"].usable[0])

    def test_100_add_a_record(self):
        self.dsdb_expect_add(NAME, self.IP)
        cmd = ['add', 'address', '--fqdn', NAME, '--ip', self.IP] + self.valid_just_tcm
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Please provide a GRN/EON_ID!", cmd)

    def test_101_add_a_record_grn(self):
        self.dsdb_expect_add(NAME, self.IP)
        cmd = ['add', 'address', '--fqdn', NAME, '--ip', self.IP,
               '--grn', GRN] + self.valid_just_tcm
        self.noouttest(cmd)
        self.dsdb_verify()

    def test_200_verify_a_record(self):
        cmd = "show address --fqdn %s" % NAME
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "DNS Record: %s" % NAME, cmd)

    def test_300_add_ns_record(self):
        cmd = ["add_ns_record", "--dns_domain", DOMAIN, "--fqdn", NAME] + self.valid_just_tcm
        self.noouttest(cmd)

    def test_305_add_ns_record_duplicate(self):
        cmd = ["add_ns_record", "--dns_domain", DOMAIN, "--fqdn", NAME] + self.valid_just_tcm
        self.badrequesttest(cmd)

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
        cmd = "show ns record --dns_domain %s --fqdn %s %s" % (DOMAIN, NAME,
                                                               DJB)
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, '.%s::%s' % (DOMAIN, NAME), cmd)

    def test_410_verify_ns_record_csv(self):
        cmd = "show ns record --dns_domain %s --fqdn %s %s" % (DOMAIN, NAME,
                                                               CSV)
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, '%s,%s' % (DOMAIN, NAME), cmd)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNSRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
