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
"""Module for testing the add shared service name command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddSharedServiceName(TestBrokerCommand):

    def test_000_no_pn_cluster(self):
        # ensure we cannot add a SharedServiceName resource to a cluster
        command = ['add_shared_service_name', '--cluster=utvcs1',
                   '--name=utvcs1pn1', '--fqdn=utvcs1pn.aqd-unittest.ms.com',
                   '--sa_aliases']
        err = self.badoptiontest(command)
        self.matchoutput(err, 'no such option: --cluster', command)

    def test_000_no_pn_host(self):
        # ensure we cannot add a SharedServiceName resource to a host
        command = ['add_shared_service_name',
                   '--hostname=evh83.aqd-unittest.ms.com',
                   '--name=utvcs1pn1', '--fqdn=utvcs1pn.aqd-unittest.ms.com',
                   '--sa_aliases']
        err = self.badoptiontest(command)
        self.matchoutput(err, 'no such option: --hostname', command)

    def test_005_add_pn_resourcegroup(self):
        # create a resourcegroup to hold a shared-service-name
        command = ['add_resourcegroup', '--resourcegroup=utvcs1ifset',
                   '--cluster=utvcs1']
        self.successtest(command)

    def test_010_no_pn_fqdn_inuse_nosa(self):
        # ensure we cannot re-use a shared-service-name FQDN already in DNS
        command = ['add_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1', '--fqdn=evh83.aqd-unittest.ms.com',
                   '--nosa_aliases']
        err = self.badrequesttest(command)
        self.matchoutput(err, 'cannot be used as a shared service name '
                              'FQDN, as DNS Record evh83.aqd-unittest.ms.com '
                              'already exists', command)

    def test_010_no_pn_fqdn_nosa(self):
        # ensure we cannot re-use a shared-service-name FQDN that is already an
        # address-alias if the sa_aliases flag is false
        command = ['add_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1',
                   '--fqdn=addralias4.aqd-unittest.ms.com',
                   '--nosa_aliases']
        err = self.badrequesttest(command)
        self.matchoutput(err, 'cannot be used as a shared service name FQDN, '
                              'as Address Alias '
                              'addralias4.aqd-unittest.ms.com already '
                              'exists', command)

    def test_010_no_pn_fqdn_inuse_sa(self):
        # ensure we cannot re-use a shared-service-name FQDN already in DNS
        # as a non-address-alias
        command = ['add_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1', '--fqdn=evh83.aqd-unittest.ms.com',
                   '--sa_aliases']
        err = self.badrequesttest(command)
        self.matchoutput(err, 'cannot be used as a shared service name FQDN, '
                              'as DNS Record evh83.aqd-unittest.ms.com '
                              'already exists', command)

    def test_015_pn_inuse_add(self):
        # check that we can use an FQDN as a shared-service-name FQDN where it
        # already exists as an address-alias
        command = ['add_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1',
                   '--fqdn=addralias4.aqd-unittest.ms.com',
                   '--sa_aliases']
        self.successtest(command)

    def test_017_pn_inuse_del(self):
        # remove the above
        command = ['del_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1']
        self.successtest(command)

    def test_020_pn_add(self):
        # add a new shared-service-name FQDN with service-address aliases
        # enabled
        command = ['add_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1', '--fqdn=utvcs1pn1.aqd-unittest.ms.com',
                   '--sa_aliases']
        self.successtest(command)

    def test_025_pn_add2(self):
        # add a second shared-service-name FQDN in its own resourcegroup with
        # service-address aliases disabled
        command = ['add_resourcegroup', '--resourcegroup=utvcs1ifset2',
                   '--cluster=utvcs1']
        self.successtest(command)

        command = ['add_shared_service_name', '--resourcegroup=utvcs1ifset2',
                   '--name=utvcs1pn2', '--fqdn=utvcs1pn2.aqd-unittest.ms.com',
                   '--nosa_aliases']
        self.successtest(command)

    def test_030_pn_nodns_nosa(self):
        # ensure we cannot add a DNS record that uses the same FQDN
        # as a shared-service-name with no-SA-aliases set
        command = ['add_address_alias',
                   '--fqdn=utvcs1pn2.aqd-unittest.ms.com',
                   '--target=arecord13.aqd-unittest.ms.com']
        err = self.badrequesttest(command)
        self.matchoutput(err, 'SharedServiceName utvcs1pn2 already exists '
                              'with the same FQDN', command)

    def test_030_pn_dns_sa(self):
        # ensure that we can add an address-alias record that uses
        # the same FQDN as a shared-service-name with SA-aliases set
        command = ['add_address_alias',
                   '--fqdn=utvcs1pn1.aqd-unittest.ms.com',
                   '--target=arecord13.aqd-unittest.ms.com']
        self.successtest(command)

    def test_035_pn_dns_sa_remove(self):
        # remove the address-alias created again the FQDN of a
        # shared-service-name resource above
        command = ['del_address_alias',
                   '--fqdn=utvcs1pn1.aqd-unittest.ms.com',
                   '--target=arecord13.aqd-unittest.ms.com']
        self.successtest(command)

    def test_040_pn_nodns_arec(self):
        # ensure we cannot add a DNS A record that uses the same FQDN
        # as a shared-service-name regardless of SA-aliases
        ip = self.net['zebra_vip'].usable[15]
        command = ['add_address', '--fqdn', 'utvcs1pn2.aqd-unittest.ms.com',
                   '--ip', ip]
        err = self.badrequesttest(command)
        self.matchoutput(err, 'SharedServiceName utvcs1pn2 already exists '
                              'with the same FQDN', command)

        command = ['add_address', '--fqdn', 'utvcs1pn1.aqd-unittest.ms.com',
                   '--ip', ip]
        err = self.badrequesttest(command)
        self.matchoutput(err, 'SharedServiceName utvcs1pn1 already exists '
                              'with the same FQDN', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
                TestAddSharedServiceName)
    unittest.TextTestRunner(verbosity=2).run(suite)
