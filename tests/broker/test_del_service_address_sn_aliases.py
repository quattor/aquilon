#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2019  Contributor
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
"""Module for testing removal of service addresses mapped back to shared
   names with address alias creation."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelServiceAddressSNAliases(TestBrokerCommand):

    def test_010_remove_sa_aa(self):
        ip = self.net['np_bucket2_vip'].usable[2]
        self.dsdb_expect_delete(ip)
        command = ['del_service_address', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1sa1']
        self.successtest(command)
        self.dsdb_verify()

    def test_010_remove_sa_noaa(self):
        ip = self.net['np_bucket2_vip'].usable[3]
        self.dsdb_expect_delete(ip)
        command = ['del_service_address', '--resourcegroup=utvcs1ifset2',
                   '--name=utvcs1sa2']
        self.successtest(command)
        self.dsdb_verify()

    def test_020_check_no_utvcs1sa1_alias(self):
        command = ['search_dns', '--fqdn=utvcs1pn1.aqd-unittest.ms.com',
                   '--fullinfo']
        out = self.commandtest(command)
        self.matchclean(out, 'Address Alias: utvcs1pn1.aqd-unittest.ms.com',
                        command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
                TestDelServiceAddressSNAliases)
    unittest.TextTestRunner(verbosity=2).run(suite)
