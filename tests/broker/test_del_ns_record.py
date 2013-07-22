#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del chassis command."""

import unittest

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from test_add_ns_record import NAME, DOMAIN


class TestDelNSRecord(TestBrokerCommand):

    def setUp(self, *args, **kwargs):
        super(TestDelNSRecord, self).setUp(*args, **kwargs)
        self.NETWORK = self.net["unknown10"]
        self.IP = str(self.net["unknown10"].usable[0])

    def test_100_delete_ns_record(self):
        cmd = "del ns_record --fqdn %s --dns_domain %s" % (NAME, DOMAIN)
        self.noouttest(cmd.split(" "))

    def test_105_delete_ns_record_nonexistent(self):
        cmd = "del ns_record --fqdn %s --dns_domain %s" % (NAME, DOMAIN)
        self.notfoundtest(cmd.split(" "))

    # although this is already tested elsewhere, just for tidyness
    def test_200_delete_a_record(self):
        self.dsdb_expect_delete(self.IP)
        cmd = "del address --fqdn %s --ip %s" % (NAME, self.IP)
        self.noouttest(cmd.split(" "))
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNSRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
