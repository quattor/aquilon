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
        self.NETWORK = self.net["ut9_chassis"]
        self.IP = str(self.net["ut9_chassis"].usable[0])

    def test_100_delete_ns_record(self):
        cmd = ["del_ns_record", "--fqdn", NAME, "--dns_domain", DOMAIN] + self.valid_just_tcm
        self.noouttest(cmd)

    def test_105_delete_ns_record_nonexistent(self):
        cmd = ["del_ns_record", "--fqdn", NAME, "--dns_domain", DOMAIN] + self.valid_just_tcm
        self.notfoundtest(cmd)

    # although this is already tested elsewhere, just for tidyness
    def test_200_delete_a_record(self):
        self.dsdb_expect_delete(self.IP)
        cmd = ["del_address", "--fqdn", NAME, "--ip", self.IP] + self.valid_just_tcm
        self.noouttest(cmd)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNSRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
