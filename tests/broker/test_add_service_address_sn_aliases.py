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
"""Module for testing adding service addresses mapped back to shared names
   with address alias creation."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddServiceAddressSNAliases(TestBrokerCommand):

    def test_000_no_sn_map_ptr(self):
        # ensure we cannot map-to-shared-name if none exists
        ip = self.net['np_bucket2_vip'].usable[2]
        command = ['add_service_address', '--cluster=utvcs1',
                   '--name=utvcs1sa1',
                   '--service_address=utvcs1sa1.aqd-unittest.ms.com',
                   '--ip', ip, '--map_to_shared_name']
        err = self.badrequesttest(command)
        self.matchoutput(err, '--map_to_shared_name specified, '
                              'but no shared service name in', command)

    def test_000_no_map_to_primary_and_shared_name(self):
        # ensure we cannot use both --map_to_primary and --map_to_shared_name
        # options.
        ip = self.net['np_bucket2_vip'].usable[2]
        command = ['add_service_address', '--cluster=utvcs1',
                   '--name=utvcs1sa1',
                   '--service_address=utvcs1sa1.aqd-unittest.ms.com',
                   '--ip', ip, '--map_to_primary', '--map_to_shared_name']
        err = self.badrequesttest(command)
        self.matchoutput(err, 'Cannot use --map_to_primary and '
                              '--map_to_shared_name together', command)

    def test_005_add_empty_resourcegroup(self):
        command = ['add_resourcegroup', '--cluster=utvcs1',
                   '--resourcegroup=utvcs1ifset3']
        self.successtest(command)

    def test_010_no_sn_map_ptr(self):
        # ensure we cannot map-to-shared-name if none in a resourcegroup
        ip = self.net['np_bucket2_vip'].usable[2]
        command = ['add_service_address', '--resourcegroup=utvcs1ifset3',
                   '--name=utvcs1sa1',
                   '--service_address=utvcs1sa1.aqd-unittest.ms.com',
                   '--ip', ip, '--map_to_shared_name']
        err = self.badrequesttest(command)
        self.matchoutput(err, '--map_to_shared_name specified, '
                              'but no shared service name in', command)

    def test_015_del_empty_resourcegroup(self):
        command = ['del_resourcegroup', '--cluster=utvcs1',
                   '--resourcegroup=utvcs1ifset3']
        self.successtest(command)

    def test_020_mapped_to_shared_name_aa(self):
        # create a service address mapped to the shared-name with
        # address alias creation
        ip = self.net['np_bucket2_vip'].usable[2]
        service_addr = 'utvcs1sa1.aqd-unittest.ms.com'
        self.dsdb_expect_add(service_addr, ip)
        command = ['add_service_address', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1sa1', '--service_address', service_addr,
                   '--ip', ip, '--map_to_shared_name']
        self.successtest(command)
        self.dsdb_verify()

    def test_020_mapped_to_shared_name_noaa(self):
        # create a service address mapped to the shared-name without
        # address alias creation
        ip = self.net['np_bucket2_vip'].usable[3]
        service_addr = 'utvcs1sa2.aqd-unittest.ms.com'
        self.dsdb_expect_add(service_addr, ip)
        command = ['add_service_address', '--resourcegroup=utvcs1ifset2',
                   '--name=utvcs1sa2', '--service_address', service_addr,
                   '--ip', ip, '--map_to_shared_name']
        self.successtest(command)
        self.dsdb_verify()

    def test_025_utvcs1pn1_addr_alias(self):
        command = ['search_dns', '--fqdn=utvcs1pn1.aqd-unittest.ms.com',
                   '--fullinfo']
        out = self.commandtest(command)
        self.matchoutput(out, 'Address Alias: utvcs1pn1.aqd-unittest.ms.com',
                         command)
        self.matchoutput(out, 'Target: utvcs1sa1.aqd-unittest.ms.com',
                         command)

    def test_025_utvcs1pn2_noaddr_alias(self):
        command = ['search_dns', '--fqdn=utvcs1pn2.aqd-unittest.ms.com',
                   '--fullinfo']
        out = self.commandtest(command)
        self.matchclean(out, 'Address Alias: utvcs1pn2.aqd-unittest.ms.com',
                        command)
        self.matchclean(out, 'Target: utvcs1sa2.aqd-unittest.ms.com', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
                TestAddServiceAddressSNAliases)
    unittest.TextTestRunner(verbosity=2).run(suite)
